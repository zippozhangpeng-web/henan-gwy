#!/usr/bin/env python3
"""
补充解析PDF格式的面试名单（商丘、洛阳、南阳、三门峡、许昌、省公安厅、省监狱）
"""
import os, sys, re, sqlite3, glob

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
SCORE_DIR = os.path.join(PROJECT_DIR, 'score_data', '2025河南省考进面名单汇总')
DB_PATH = os.path.join(PROJECT_DIR, 'gwy_data.db')

HEADER_WORDS = {'附件1','姓名','准考证号','报考单位','职位代码','行测','成绩','申论','公安','总成绩','名次','备注','备注说明'}


def parse_one_pdf(filepath):
    """解析单个PDF面试名单文件"""
    import fitz
    doc = fitz.open(filepath)
    
    # 提取纯文本行
    all_lines = []
    for p in range(doc.page_count):
        text = doc[p].get_text()
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        all_lines.extend(lines)
    doc.close()
    
    # 过滤掉表头行
    data_lines = [l for l in all_lines if l not in HEADER_WORDS]
    
    # 找记录：每8行为一组（姓名、准考证号、单位、职位代码、行测、申论、公安、总成绩）
    scores = {}
    i = 0
    while i + 7 < len(data_lines):
        name = data_lines[i]
        ticket = data_lines[i+1]
        unit = data_lines[i+2]
        code = data_lines[i+3]
        xingce = data_lines[i+4]
        shenlun = data_lines[i+5]
        gongan = data_lines[i+6]
        total = data_lines[i+7]
        
        # 校验：职位代码必须是8位数字
        if re.match(r'^\d{8}$', code):
            try:
                score_val = float(total)
                if score_val > 0 and score_val < 100:
                    if code not in scores:
                        scores[code] = []
                    scores[code].append(score_val)
                    i += 8
                    continue
            except: pass
        
        i += 1
    
    return scores


def parse_pdfs():
    """解析所有PDF文件"""
    all_scores = {}
    
    pdf_files = sorted(glob.glob(os.path.join(SCORE_DIR, '*.pdf')))
    print(f'📄 共 {len(pdf_files)} 个PDF文件')
    
    for fp in pdf_files:
        fname = os.path.basename(fp)
        try:
            scores = parse_one_pdf(fp)
            # 提取城市名
            city_match = re.search(r'(商丘|洛阳|南阳|三门峡|许昌|省公安厅|省监狱|教育考试)', fname)
            city = city_match.group(1) if city_match else fname[:8]
            print(f'  ✅ [{city:6s}] {len(scores)} 个职位代码 (来自PDF)')
            for k, v in scores.items():
                if k not in all_scores:
                    all_scores[k] = []
                all_scores[k].extend(v)
        except Exception as e:
            print(f'  ❌ [{fname[:12]}] {e}')
    
    print(f'\n📊 PDF共解析 {len(all_scores)} 个新职位代码')
    return all_scores


def merge_to_db(all_scores):
    """将PDF解析的结果合并到数据库"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    updated = 0
    
    for code, sc_list in all_scores.items():
        mn = round(min(sc_list), 2)
        mx = round(max(sc_list), 2)
        av = round(sum(sc_list)/len(sc_list), 2)
        
        # 只更新还没有分数的岗位（已经有分数的说明已在之前XLS解析中覆盖）
        c.execute('''UPDATE positions SET min_score=COALESCE(min_score,?),
                     max_score=COALESCE(max_score,?),
                     avg_score=COALESCE(avg_score,?)
                     WHERE year=2025 AND position_code=? AND min_score IS NULL''',
                  (mn, mx, av, code))
        if c.rowcount > 0:
            updated += c.rowcount
        else:
            # 模糊匹配
            c.execute('''UPDATE positions SET min_score=COALESCE(min_score,?),
                         max_score=COALESCE(max_score,?),
                         avg_score=COALESCE(avg_score,?)
                         WHERE year=2025 AND position_code LIKE ? AND min_score IS NULL''',
                      (mn, mx, av, code[:6] + '%'))
            if c.rowcount > 0:
                updated += c.rowcount
    
    conn.commit()
    
    c.execute('SELECT COUNT(*) FROM positions WHERE year=2025 AND min_score IS NOT NULL')
    scored = c.fetchone()[0]
    c.execute('SELECT COUNT(*) FROM positions WHERE year=2025')
    total = c.fetchone()[0]
    conn.close()
    
    print(f'\n✅ PDF合并完成！补充更新 {updated} 条')
    print(f'📋 2025年总覆盖率: {scored}/{total} ({scored*100/total:.1f}%)')
    return scored


def recalc_scores():
    """重新计算四维评分（用新分数数据）"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # 更新分数时重新计算难度评分
    rows = c.execute('''SELECT ps.position_id, p.min_score, p.city, p.recruit_num, p.education,
                         p.political_status, p.experience_requirement
                        FROM position_scores ps
                        JOIN positions p ON p.id = ps.position_id
                        WHERE p.min_score IS NOT NULL''').fetchall()
    
    recalc = 0
    for pid, mn, city, num, edu, pol, exp in rows:
        # 只调整难度分数，其他维度不变
        d = 5.0
        if mn >= 70: d += 2.5
        elif mn >= 67: d += 1.5
        elif mn >= 64: d += 0.5
        elif mn > 0 and mn < 58: d -= 1.0
        if city == '郑州': d += 2.0
        elif city in ('洛阳','南阳','新乡'): d += 1.0
        if num == 1: d += 1.5
        elif num <= 2: d += 0.5
        elif num >= 5: d -= 1.0
        if '硕士' in edu: d -= 0.5
        if pol and '党员' in pol: d -= 0.5
        d = round(max(1, min(10, d)), 1)
        
        # 重算综合分
        c.execute('''SELECT region_score, salary_score, prospect_score 
                     FROM position_scores WHERE position_id=?''', (pid,))
        row = c.fetchone()
        if row:
            r, s, p = row
            ov = round((d + r + s + p) / 4, 1)
            c.execute('UPDATE position_scores SET difficulty_score=?, overall_score=? WHERE position_id=?',
                      (d, ov, pid))
            recalc += 1
    
    conn.commit()
    conn.close()
    print(f'📊 重算 {recalc} 个岗位的难度评分')
    return recalc


def main():
    print('=' * 60)
    print('🏛️  PDF面试名单解析 & 四维评分更新')
    print('=' * 60)
    
    if not os.path.exists(SCORE_DIR):
        print(f'❌ 目录不存在: {SCORE_DIR}')
        sys.exit(1)
    
    print('\n📥 Step 1: 解析PDF面试名单...')
    all_scores = parse_pdfs()
    
    if not all_scores:
        print('⚠️  无新数据')
        sys.exit(0)
    
    print('\n🗄️  Step 2: 合并到数据库...')
    merge_to_db(all_scores)
    
    print('\n📊 Step 3: 更新四维评分...')
    recalc_scores()
    
    print(f'\n🎉 完成!')


if __name__ == '__main__':
    main()
