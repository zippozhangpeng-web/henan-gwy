#!/usr/bin/env python3
"""补抓缺失数据：新乡XLSX + 省直/监狱等 offcn 页面"""
import os, sys, re, sqlite3, requests, openpyxl
from html.parser import HTMLParser

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
SCORE_DIR = os.path.join(PROJECT_DIR, 'score_data', '2025河南省考进面名单汇总')
DB_PATH = os.path.join(PROJECT_DIR, 'gwy_data.db')

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}


def parse_xinxiang():
    """解析新乡XLSX"""
    fp = os.path.join(SCORE_DIR, '2025年全省统考公务员新乡市职位参加面试确认人员名单.xlsx')
    if not os.path.exists(fp): return {}
    wb = openpyxl.load_workbook(fp, data_only=True)
    s = wb.active
    scores = {}
    for row in s.iter_rows(min_row=3, values_only=True):
        vals = [str(c).strip() if c else '' for c in row]
        if len(vals) < 11: continue
        code = vals[5].strip().replace('.0', '')
        score_str = vals[10].strip()  # 笔试成绩
        if not code or not re.match(r'^\d{8}$', code): continue
        try:
            sv = float(score_str)
            scores.setdefault(code, []).append(sv)
        except: pass
    wb.close()
    return scores


def scrape_offcn_dept(dept_url):
    """从offcn单个详情页抓取分数（格式：表格中有职位代码和进面分数）"""
    try:
        resp = requests.get(dept_url, headers=HEADERS, timeout=15)
        if resp.status_code != 200: return {}
    except: return {}

    html = resp.text
    scores = {}

    # 模式1: 表格中有 职位代码 和 进面最低分/最高分
    # offcn的详情页通常有 <table> 或 <dl> 结构
    # 找 <td> 中包含职位代码和分数的行
    patterns = [
        # 模式: "职位代码: XXXXX" "进面最低分: XX"
        r'职位代码[：:]\s*(\d{8})[^。]*?最低[^0-9]*?(\d+\.?\d*)',
        r'职位代码[：:]\s*(\d{8}).*?(\d+\.?\d*)\s*分',
        # 更宽松的
        r'(\d{8})\s*[^<]*?(\d+\.\d+)\s*分',
    ]
    for pat in patterns:
        for m in re.finditer(pat, html, re.DOTALL):
            code, score = m.group(1), m.group(2)
            try:
                sv = float(score)
                if 0 < sv < 100 and len(code) == 8:
                    scores.setdefault(code, []).append(sv)
            except: pass

    # 模式2: 无检测到 → 尝试解析html表格
    if not scores:
        table_scores = parse_html_table(html)
        scores.update(table_scores)

    return scores


def parse_html_table(html):
    """从HTML表格中提取职位代码和分数"""
    scores = {}
    # 找表格
    tables = re.findall(r'<table[^>]*>(.*?)</table>', html, re.DOTALL)
    for tbl in tables:
        rows = re.findall(r'<tr[^>]*>(.*?)</tr>', tbl, re.DOTALL)
        for row in rows:
            cells = re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>', row, re.DOTALL)
            texts = [re.sub(r'<[^>]+>', '', c).strip() for c in cells]
            # 找包含8位数字的行
            code = None
            for t in texts:
                m = re.search(r'(\d{8})', t)
                if m: code = m.group(1); break
            if not code: continue
            # 找分数
            for t in texts:
                nums = re.findall(r'(\d+\.\d+)', t)
                for n in nums:
                    sv = float(n)
                    if 20 < sv < 100:
                        scores.setdefault(code, []).append(sv)
                        break
    return scores


def main():
    print('=' * 60)
    print('补抓缺失数据：新乡 + 省直(offcn.com)')
    print('=' * 60)

    all_scores = {}

    # Step 1: 新乡XLSX
    print('\n📥 Step 1: 新乡...')
    xx_scores = parse_xinxiang()
    print(f'  新乡: {len(xx_scores)} 个职位代码')
    all_scores.update(xx_scores)

    # Step 2: 省直单位 - offcn页面
    print('\n📥 Step 2: 省直单位(offcn)...')
    # 从汇总页面获取所有省直单位详情链接
    dept_pages = [
        # 省直单位 - 直接从之前看到的详情页抓
        # 这些是 offcn 上省直单位的详情页
        ('财政厅预算评审中心', 'https://he.offcn.com/html/2025/08/322314.html'),
        ('财政厅社保基金管理中心', 'https://he.offcn.com/html/2025/08/322315.html'),
        ('财政厅PPP管理中心', 'https://he.offcn.com/html/2025/08/322316.html'),
        ('财政厅国有金融资本', 'https://he.offcn.com/html/2025/08/322317.html'),
        ('财政厅预算绩效评价', 'https://he.offcn.com/html/2025/08/322310.html'),
        ('测绘地理信息技术中心', 'https://he.offcn.com/html/2025/08/322313.html'),
        ('河南省档案馆', 'https://he.offcn.com/html/2025/08/322312.html'),
        ('发改委', 'https://he.offcn.com/html/2025/09/324126.html'),
        ('妇联', 'https://he.offcn.com/html/2025/09/324127.html'),
        ('高级人民法院', 'https://he.offcn.com/html/2025/09/324128.html'),
        ('公安厅', 'https://he.offcn.com/html/2025/09/324129.html'),
        ('疾控局', 'https://he.offcn.com/html/2025/09/324130.html'),
        ('教育考试院', 'https://he.offcn.com/html/2025/09/324131.html'),
        ('救助管理事务中心', 'https://he.offcn.com/html/2025/09/324132.html'),
        ('科技厅', 'https://he.offcn.com/html/2025/09/324133.html'),
        ('林业局', 'https://he.offcn.com/html/2025/09/324134.html'),
        ('林业技术工作总站', 'https://he.offcn.com/html/2025/09/324135.html'),
        ('人民检察院', 'https://he.offcn.com/html/2025/09/324136.html'),
        ('驻北京办事处', 'https://he.offcn.com/html/2025/09/324137.html'),
        ('散装水泥发展中心', 'https://he.offcn.com/html/2025/09/324138.html'),
        ('商务厅', 'https://he.offcn.com/html/2025/09/324139.html'),
        ('商务厅电子商务', 'https://he.offcn.com/html/2025/09/324144.html'),
        ('生态环境厅', 'https://he.offcn.com/html/2025/09/324145.html'),
        ('生态环境厅第三办', 'https://he.offcn.com/html/2025/09/324146.html'),
        ('生态环境厅第四办', 'https://he.offcn.com/html/2025/09/324147.html'),
        ('生态环境厅第五办', 'https://he.offcn.com/html/2025/09/324148.html'),
        ('市场监管局', 'https://he.offcn.com/html/2025/09/324149.html'),
        ('司法厅', 'https://he.offcn.com/html/2025/09/324150.html'),
        ('统计局', 'https://he.offcn.com/html/2025/09/324151.html'),
        ('卫生健康委', 'https://he.offcn.com/html/2025/09/324152.html'),
        ('文物局', 'https://he.offcn.com/html/2025/09/324153.html'),
        ('药监局', 'https://he.offcn.com/html/2025/09/324154.html'),
        ('监狱管理局', 'https://he.offcn.com/html/2025/09/324155.html'),
        ('行政审批和政务信息', 'https://he.offcn.com/html/2025/09/324156.html'),
        ('医保局', 'https://he.offcn.com/html/2025/09/324157.html'),
        ('应急管理厅', 'https://he.offcn.com/html/2025/09/324158.html'),
        ('政府办公厅', 'https://he.offcn.com/html/2025/09/324159.html'),
        ('住建厅', 'https://he.offcn.com/html/2025/09/324160.html'),
        ('自然资源厅', 'https://he.offcn.com/html/2025/09/324161.html'),
        ('机关事务管理局', 'https://he.offcn.com/html/2025/10/324401.html'),
        ('河南省委组织部', 'https://he.offcn.com/html/2025/10/324403.html'),
        ('河南省委社会工作部', 'https://he.offcn.com/html/2025/10/324404.html'),
        ('河南省工信厅', 'https://he.offcn.com/html/2025/10/324405.html'),
        ('河南省工商联', 'https://he.offcn.com/html/2025/10/324406.html'),
        ('河南省审计厅', 'https://he.offcn.com/html/2025/10/324407.html'),
        ('河南省民委', 'https://he.offcn.com/html/2025/10/324408.html'),
        ('河南省信访局', 'https://he.offcn.com/html/2025/10/324409.html'),
        ('河南省社科联', 'https://he.offcn.com/html/2025/10/324410.html'),
        ('河南省总工会', 'https://he.offcn.com/html/2025/10/324411.html'),
        ('河南省交通运输厅', 'https://he.offcn.com/html/2025/10/324412.html'),
        ('河南省农业农村厅', 'https://he.offcn.com/html/2025/10/324413.html'),
        ('河南省水利厅', 'https://he.offcn.com/html/2025/10/324414.html'),
        ('河南省退役军人事务厅', 'https://he.offcn.com/html/2025/10/324415.html'),
        ('河南省文化和旅游厅', 'https://he.offcn.com/html/2025/10/324416.html'),
        ('河南省人防办', 'https://he.offcn.com/html/2025/10/324417.html'),
        ('河南省财政厅', 'https://he.offcn.com/html/2025/10/324418.html'),
        ('河南省地方金融管理局', 'https://he.offcn.com/html/2025/10/324419.html'),
        ('河南省监狱', 'https://he.offcn.com/html/2025/09/324155.html'),
    ]

    for name, url in dept_pages:
        try:
            ss = scrape_offcn_dept(url)
            if ss:
                codes_str = ', '.join(list(ss.keys())[:3])
                print(f'  ✅ [{name}] {len(ss)} 个 ({codes_str}...)')
                for k, v in ss.items():
                    all_scores.setdefault(k, []).extend(v)
            else:
                print(f'  ⚠️  [{name}] 0 个')
        except Exception as e:
            print(f'  ❌ [{name}] {e}')

    print(f'\n📊 共 {len(all_scores)} 个不同职位代码')

    if not all_scores:
        print('无新数据')
        return

    # 更新DB
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    updated = 0
    for code, sc_list in all_scores.items():
        if not sc_list: continue
        mn = round(min(sc_list), 2)
        mx = round(max(sc_list), 2)
        av = round(sum(sc_list)/len(sc_list), 2)
        c.execute('''UPDATE positions SET min_score=COALESCE(min_score,?),
            max_score=COALESCE(max_score,?),
            avg_score=COALESCE(avg_score,?)
            WHERE year=2025 AND position_code LIKE ? AND min_score IS NULL''',
            (mn, mx, av, code[:6] + '%'))
        updated += c.rowcount
    conn.commit()

    c.execute("SELECT COUNT(*) FROM positions WHERE year=2025 AND min_score IS NOT NULL")
    scored = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM positions WHERE year=2025")
    total = c.fetchone()[0]
    conn.close()

    print(f'✅ 更新 {updated} 条')
    print(f'📊 2025年覆盖率: {scored}/{total} ({scored*100/total:.1f}%)')
    print('🎉 完成!')


if __name__ == '__main__':
    main()
