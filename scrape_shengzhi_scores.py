#!/usr/bin/env python3
"""
从本地宝省直汇总页抓取各单位的面试确认名单附件（xcoss.henan.gov.cn .doc/.xls）
"""
import os, sys, re, sqlite3, requests, subprocess

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(PROJECT_DIR, 'gwy_data.db')
DL_DIR = os.path.join(PROJECT_DIR, 'score_data', '省直附件')
os.makedirs(DL_DIR, exist_ok=True)

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}


def get_attachment_urls_from_article(article_url):
    """从本地宝省直单位详情页中提取xcoss.henan.gov.cn的附件链接"""
    try:
        resp = requests.get(article_url, headers=HEADERS, timeout=15)
        if resp.status_code != 200: return []
    except: return []
    
    # 找 xcoss.henan.gov.cn 的链接
    urls = re.findall(r'https://xcoss\.henan\.gov\.cn[^\"\'<>]+', resp.text)
    # 保留附件1（面试确认人员名单）- 通常是第一个
    deduped = []
    seen = set()
    for u in urls:
        if u not in seen:
            deduped.append(u)
            seen.add(u)
    return deduped


def parse_doc_or_xls(filepath):
    """解析 doc/xls/xlsx 文件，提取职位代码和分数"""
    ext = os.path.splitext(filepath)[1].lower()
    scores = {}
    
    if ext == '.xls':
        import xlrd
        try:
            wb = xlrd.open_workbook(filepath)
            s = wb.sheet_by_index(0)
            # 找包含'职位代码'和'总成绩'的行
            hr = None
            for r in range(min(10, s.nrows)):
                row = [str(s.cell_value(r,c)).strip() for c in range(s.ncols)]
                rt = ''.join(row)
                if '职位代码' in rt and ('总成绩' in rt or '笔试成绩' in rt):
                    hr = r; break
            if hr is None:
                # 省厅doc可能转成xls格式不同
                return parse_generic_xls(s)
            code_col = score_col = None
            for c in range(s.ncols):
                cl = str(s.cell_value(hr,c)).strip().replace('\n','')
                if '职位代码' in cl: code_col = c
                if '总成绩' in cl or '笔试成绩' in cl: score_col = c
            if code_col is None: return scores
            for r in range(hr+1, s.nrows):
                code = str(s.cell_value(r, code_col)).strip().replace('.0','')
                if not re.match(r'^\d{8}$', code): continue
                if score_col is not None:
                    try:
                        sv = float(s.cell_value(r, score_col))
                        if 0 < sv < 100: scores.setdefault(code, []).append(sv)
                    except: pass
        except: pass
    elif ext == '.doc':
        # doc文件 - 用python的catdoc或尝试文本提取
        try:
            # 尝试用textutil (macOS) 提取文本
            txt_path = filepath + '.txt'
            subprocess.run(['textutil', '-convert', 'txt', '-output', txt_path, filepath], 
                          capture_output=True, timeout=30)
            if os.path.exists(txt_path):
                with open(txt_path, 'r', encoding='utf-8', errors='ignore') as f:
                    text = f.read()
                os.remove(txt_path)
                scores = parse_doc_text(text)
        except: pass
    
    return scores


def parse_generic_xls(sheet):
    """通用解析 - 找包含8位数字的列当作职位代码，找分数值"""
    scores = {}
    for r in range(sheet.nrows):
        row = [str(sheet.cell_value(r,c)).strip() for c in range(sheet.ncols)]
        code = None
        for c, v in enumerate(row):
            m = re.match(r'^(\d{8})$', v)
            if m: code = m.group(1); break
        if not code: continue
        # 找分数
        for v in row:
            try:
                sv = float(v)
                if 20 < sv < 100:
                    scores.setdefault(code, []).append(sv)
                    break
            except: pass
    return scores


def parse_doc_text(text):
    """从纯文本中提取职位代码和分数"""
    scores = {}
    lines = text.split('\n')
    cur_code = None
    for line in lines:
        line = line.strip()
        m = re.search(r'(\d{8})', line)
        if m: cur_code = m.group(1)
        # 找分数
        nums = re.findall(r'(\d+\.\d+)', line)
        for n in nums:
            sv = float(n)
            if 30 < sv < 100 and cur_code and re.match(r'^\d{8}$', cur_code):
                scores.setdefault(cur_code, []).append(sv)
    return scores


def main():
    import urllib.request, urllib.parse
    
    print('='*60)
    print('省直单位面试名单附件收集')
    print('='*60)
    
    # 省直单位详情页URL (从本地宝汇总页提取)
    shengzhi_urls = [
        'https://m.zz.bendibao.com/job/140879.shtm',  # 科技厅
        'https://m.zz.bendibao.com/job/140878.shtm',  # 工信厅
        'https://m.zz.bendibao.com/job/140871.shtm',  # 住建厅
        'https://m.zz.bendibao.com/job/140869.shtm',  # 教育考试院
        'https://m.zz.bendibao.com/job/140868.shtm',  # 公安厅
        'https://m.zz.bendibao.com/job/140867.shtm',  # 信访局
        'https://m.zz.bendibao.com/job/140930.shtm',  # 统计局
        'https://m.zz.bendibao.com/job/140920.shtm',  # 商务厅
        'https://m.zz.bendibao.com/job/140921.shtm',  # 商务厅电子商务
        'https://m.zz.bendibao.com/job/140922.shtm',  # 散装水泥
        'https://m.zz.bendibao.com/job/140923.shtm',  # 驻京办
        'https://m.zz.bendibao.com/job/140924.shtm',  # 水利厅
        'https://m.zz.bendibao.com/job/140925.shtm',  # 司法厅
        'https://m.zz.bendibao.com/job/140926.shtm',  # 救助中心
        'https://m.zz.bendibao.com/job/140927.shtm',  # 高院
        'https://m.zz.bendibao.com/job/140928.shtm',  # 台办
        'https://m.zz.bendibao.com/job/140929.shtm',  # 民盟
        'https://m.zz.bendibao.com/job/140919.shtm',  # 统战部
        'https://m.zz.bendibao.com/job/140960.shtm',  # 疾控局
        'https://m.zz.bendibao.com/job/140959.shtm',  # 体育局
        'https://m.zz.bendibao.com/job/140957.shtm',  # 林业局
        'https://m.zz.bendibao.com/job/140956.shtm',  # 市场监管局
        'https://m.zz.bendibao.com/job/140955.shtm',  # 生态环境厅
        'https://m.zz.bendibao.com/job/140954.shtm',  # 总工会
        'https://m.zz.bendibao.com/job/140953.shtm',  # 外事办
        'https://m.zz.bendibao.com/job/140952.shtm',  # 发改委
        'https://m.zz.bendibao.com/job/140951.shtm',  # 财政厅
        'https://m.zz.bendibao.com/job/140950.shtm',  # 测绘中心
        'https://m.zz.bendibao.com/job/140949.shtm',  # 政府国资委
        'https://m.zz.bendibao.com/job/140993.shtm',  # 检察院
        'https://m.zz.bendibao.com/job/140991.shtm',  # 药监局
        'https://m.zz.bendibao.com/job/140990.shtm',  # 档案馆
        'https://m.zz.bendibao.com/job/140989.shtm',  # 党校
        'https://m.zz.bendibao.com/job/140988.shtm',  # 妇联
        'https://m.zz.bendibao.com/job/140987.shtm',  # 编办
    ]
    
    all_scores = {}
    all_downloaded = []
    
    print(f'\n📥 共 {len(shengzhi_urls)} 个省直单位\n')
    
    for url in shengzhi_urls:
        # 提取单位名
        m = re.search(r'/job/\d+\.shtm', url)
        name = url.split('/')[-1].replace('.shtm','')[:12]
        
        # 获取附件链接
        attachments = get_attachment_urls_from_article(url)
        if not attachments:
            print(f'  ⚠️  [{name}] 未找到附件')
            continue
        
        print(f'  📤 [{name}] {len(attachments)} 个附件')
        
        for att_url in attachments:
            ext = os.path.splitext(att_url.split('?')[0])[1].lower()
            if ext not in ('.xls', '.xlsx', '.doc', '.docx'): continue
            
            fname = f'{name}{ext}'
            fp = os.path.join(DL_DIR, fname)
            
            try:
                resp = requests.get(att_url, headers=HEADERS, timeout=60)
                with open(fp, 'wb') as f: f.write(resp.content)
                all_downloaded.append(fp)
                
                # 解析
                scores = parse_doc_or_xls(fp)
                if scores:
                    print(f'    ✅ {len(scores)} 个职位代码')
                    for k, v in scores.items():
                        all_scores.setdefault(k, []).extend(v)
            except Exception as e:
                print(f'    ❌ {e}')
    
    print(f'\n📊 共下载 {len(all_downloaded)} 个附件，解析 {len(all_scores)} 个职位')
    
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
        # 模糊匹配
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
    print(f'📊 覆盖率: {scored}/{total} ({scored*100/total:.1f}%)')


if __name__ == '__main__':
    main()
