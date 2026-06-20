#!/usr/bin/env python3
"""
河南省考面试分数数据导入 + 四维评分计算
"""
import os, sys, sqlite3
import xlrd, openpyxl

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
SCORE_DIR = os.path.join(PROJECT_DIR, 'score_data', '2025河南省考进面名单汇总')
DB_PATH = os.path.join(PROJECT_DIR, 'gwy_data.db')

CITY_DATA = {
    '郑州': {'gdp_rank': 1,'gdp': 14370,'population': 1282,'avg_salary': 8500,'house_price': 14000,'is_capital': True},
    '洛阳': {'gdp_rank': 2,'gdp': 5820,'population': 707,'avg_salary': 6800,'house_price': 8500},
    '南阳': {'gdp_rank': 3,'gdp': 4710,'population': 971,'avg_salary': 5500,'house_price': 6500},
    '许昌': {'gdp_rank': 4,'gdp': 3530,'population': 438,'avg_salary': 6000,'house_price': 6200},
    '周口': {'gdp_rank': 5,'gdp': 3500,'population': 885,'avg_salary': 5200,'house_price': 5500},
    '新乡': {'gdp_rank': 6,'gdp': 3460,'population': 625,'avg_salary': 5800,'house_price': 7000},
    '驻马店': {'gdp_rank': 7,'gdp': 3220,'population': 700,'avg_salary': 5000,'house_price': 5000},
    '商丘': {'gdp_rank': 8,'gdp': 3100,'population': 781,'avg_salary': 5300,'house_price': 5800},
    '信阳': {'gdp_rank': 9,'gdp': 3060,'population': 623,'avg_salary': 5100,'house_price': 5500},
    '平顶山': {'gdp_rank': 10,'gdp': 2820,'population': 498,'avg_salary': 5500,'house_price': 5800},
    '开封': {'gdp_rank': 11,'gdp': 2710,'population': 457,'avg_salary': 5600,'house_price': 6200},
    '安阳': {'gdp_rank': 12,'gdp': 2580,'population': 548,'avg_salary': 5400,'house_price': 5800},
    '焦作': {'gdp_rank': 13,'gdp': 2310,'population': 354,'avg_salary': 5600,'house_price': 5500},
    '濮阳': {'gdp_rank': 14,'gdp': 2040,'population': 377,'avg_salary': 5300,'house_price': 5500},
    '漯河': {'gdp_rank': 15,'gdp': 1880,'population': 236,'avg_salary': 5400,'house_price': 5200},
    '三门峡': {'gdp_rank': 16,'gdp': 1780,'population': 227,'avg_salary': 5600,'house_price': 5000},
    '鹤壁': {'gdp_rank': 17,'gdp': 1050,'population': 157,'avg_salary': 5200,'house_price': 4800},
    '济源': {'gdp_rank': 18,'gdp': 830,'population': 73,'avg_salary': 5500,'house_price': 5000},
}


def auto_detect_cols(header_cells):
    """自动检测职位代码列和总成绩列"""
    code_col, score_col = 0, -1
    for i, c in enumerate(header_cells):
        cl = c.replace('\n','').replace(' ','')
        if '职位代码' in cl or '报考单位代码' in cl:
            code_col = i
        if '总成绩' in cl or '总分' in cl:
            score_col = i
    # 如果没找到总成绩列，尝试找包含"成绩"的最后一列
    if score_col < 0:
        for i in range(len(header_cells)-1, -1, -1):
            if '成绩' in header_cells[i]:
                score_col = i
                break
    if score_col < 0:
        score_col = len(header_cells) - 1
    return code_col, score_col


def find_file(keyword):
    for f in os.listdir(SCORE_DIR):
        if keyword in f:
            return os.path.join(SCORE_DIR, f)
    return None


def parse_all():
    """解析所有面试名单文件"""
    all_scores = {}
    
    for fname in sorted(os.listdir(SCORE_DIR)):
        fp = os.path.join(SCORE_DIR, fname)
        if os.path.isdir(fp) or fname.startswith('.'):
            continue
        ext = os.path.splitext(fname)[1].lower()
        if ext not in ('.xls', '.xlsx'):
            continue
        
        try:
            if ext == '.xls':
                wb = xlrd.open_workbook(fp)
                s = wb.sheet_by_index(0)
                # 找表头行
                hrow = None
                for r in range(min(8, s.nrows)):
                    row_vals = [str(s.cell_value(r,c)).strip() for c in range(s.ncols)]
                    row_text = ''.join(row_vals)
                    if '职位代码' in row_text and '总成绩' in row_text:
                        hrow = r
                        code_col, score_col = auto_detect_cols(row_vals)
                        break
                
                if hrow is None:
                    print(f'  ⚠️  [{fname[:8]}] 未找到表头行')
                    continue
                
                city_name = fname.split('市')[0][-3:] if '市' in fname else fname[:6]
                count = 0
                for r in range(hrow + 1, s.nrows):
                    code = str(s.cell_value(r, code_col)).strip().replace('.0', '')
                    score_str = str(s.cell_value(r, score_col)).strip()
                    try:
                        score = float(score_str)
                        if len(code) >= 5:
                            if code not in all_scores:
                                all_scores[code] = []
                                count += 1
                            all_scores[code].append(score)
                    except: pass
                print(f'  ✅ [{city_name:6s}] {count} 个职位代码')
                
            else:  # xlsx
                wb = openpyxl.load_workbook(fp, data_only=True)
                s = wb.active
                hrow = None
                for r_idx, row in enumerate(s.iter_rows(min_row=1, max_row=8, values_only=True)):
                    row_vals = [str(c).strip() if c else '' for c in row]
                    row_text = ''.join(row_vals)
                    if '职位代码' in row_text and '总成绩' in row_text:
                        hrow = r_idx
                        code_col, score_col = auto_detect_cols(row_vals)
                        break
                
                if hrow is None:
                    print(f'  ⚠️  [{fname[:8]}] 未找到表头行')
                    wb.close()
                    continue
                
                city_name = fname.split('市')[0][-3:] if '市' in fname else fname[:6]
                count = 0
                for row in s.iter_rows(min_row=hrow + 2, values_only=True):
                    vals = [str(c).strip().replace('.0', '') if c else '' for c in row]
                    if len(vals) <= max(code_col, score_col):
                        continue
                    code = vals[code_col]
                    score_str = vals[score_col]
                    if not code or not score_str: continue
                    try:
                        score = float(score_str)
                        if len(code) >= 5:
                            if code not in all_scores:
                                all_scores[code] = []
                                count += 1
                            all_scores[code].append(score)
                    except: pass
                print(f'  ✅ [{city_name:6s}] {count} 个职位代码')
                wb.close()
                
        except Exception as e:
            print(f'  ❌ [{fname[:12]}] {e}')
    
    return all_scores


def import_scores_to_db(all_scores):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    updated, matched = 0, 0
    
    for code, sc_list in all_scores.items():
        mn = round(min(sc_list), 2)
        mx = round(max(sc_list), 2)
        av = round(sum(sc_list)/len(sc_list), 2)
        
        # 精确匹配
        c.execute('UPDATE positions SET min_score=?, max_score=?, avg_score=? WHERE year=2025 AND position_code=?',
                  (mn, mx, av, code))
        if c.rowcount > 0:
            updated += c.rowcount
            matched += 1
        else:
            # 模糊匹配前6位
            c.execute('UPDATE positions SET min_score=?, max_score=?, avg_score=? WHERE year=2025 AND position_code LIKE ?',
                      (mn, mx, av, code[:6] + '%'))
            if c.rowcount > 0:
                updated += c.rowcount
    
    conn.commit()
    c.execute('SELECT COUNT(*) FROM positions WHERE year=2025 AND min_score IS NOT NULL')
    scored = c.fetchone()[0]
    c.execute('SELECT COUNT(*) FROM positions WHERE year=2025')
    total = c.fetchone()[0]
    conn.close()
    print(f'\n✅ 分数导入: {matched} 个代码匹配, 更新 {updated} 条')
    print(f'📋 2025年有分数: {scored}/{total} ({scored*100/total:.1f}%)')
    return scored


def calc_all_scores():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    rows = c.execute('''SELECT id, city, system_type, education, recruit_num, 
                         experience_requirement, political_status, 
                         COALESCE(min_score, 0), unit
                        FROM positions''').fetchall()
    c.execute('DELETE FROM position_scores')
    cnt = 0
    
    for row in rows:
        pid, city, st, edu, num, exp, pol, mn, unit = row
        cd = CITY_DATA.get(city)
        
        # 维度1: 难度 1-10
        d = 5.0
        if mn > 0:
            if mn >= 70: d += 2.5
            elif mn >= 67: d += 1.5
            elif mn >= 64: d += 0.5
            elif mn < 58: d -= 1.0
        if city == '郑州': d += 2.0
        elif city in ('洛阳','南阳','新乡'): d += 1.0
        if num == 1: d += 1.5
        elif num <= 2: d += 0.5
        elif num >= 5: d -= 1.0
        if '硕士' in edu: d -= 0.5
        if pol and '党员' in pol: d -= 0.5
        d = round(max(1, min(10, d)), 1)
        
        # 维度2: 地区 1-10
        if cd:
            if city == '郑州': r = 9.5
            elif cd['gdp_rank'] <= 3: r = 8.0
            elif cd['gdp_rank'] <= 6: r = 7.0
            elif cd['gdp_rank'] <= 10: r = 6.0
            elif cd['gdp_rank'] <= 14: r = 5.5
            else: r = 5.0
        else: r = 5.0
        
        # 维度3: 薪酬 1-10
        if cd:
            s = cd['avg_salary'] / 1000
            if '公安' in st: s += 0.8
            elif st in ('法院系统','检察院系统'): s += 0.7
            elif st in ('纪委监委','财政系统'): s += 0.5
            s = round(max(1, min(10, s)), 1)
        else: s = 5.0
        
        # 维度4: 前景 1-10
        if '党委' in st: p = 8.5
        elif st in ('政府办公室','纪委监委'): p = 8.0
        elif st in ('公安系统','法院系统','检察院系统','财政系统'): p = 7.5
        elif '乡镇' in st: p = 4.0
        else: p = 6.0
        if city == '郑州': p += 0.5
        p = round(max(1, min(10, p)), 1)
        
        ov = round((d + r + s + p) / 4, 1)
        c.execute('''INSERT OR REPLACE INTO position_scores 
            (position_id, difficulty_score, region_score, salary_score, prospect_score, overall_score)
            VALUES (?,?,?,?,?,?)''', (pid, d, r, s, p, ov))
        cnt += 1
    
    conn.commit()
    print(f'✅ 四维评分: {cnt} 个岗位')
    
    # 统计
    print(f'\n📊 各系统平均评分 (TOP 10):')
    rows = c.execute('''SELECT p.system_type, ROUND(AVG(ps.overall_score),1),
        ROUND(AVG(ps.difficulty_score),1), ROUND(AVG(ps.region_score),1),
        ROUND(AVG(ps.salary_score),1), ROUND(AVG(ps.prospect_score),1), COUNT(*)
        FROM position_scores ps JOIN positions p ON p.id=ps.position_id
        GROUP BY p.system_type ORDER BY AVG(ps.overall_score) DESC LIMIT 10''').fetchall()
    for r in rows:
        print(f'  {r[0]:10s} | 综合{r[1]} 难度{r[2]} 地区{r[3]} 薪酬{r[4]} 前景{r[5]} | {r[6]}个')
    conn.close()


def main():
    print('='*60)
    print('🏛️  面试分数导入 & 四维评分')
    print('='*60)
    
    if not os.path.exists(SCORE_DIR):
        print(f'❌ 目录不存在: {SCORE_DIR}')
        sys.exit(1)
    
    print('\n📥 Step 1: 自动解析面试名单...')
    all_scores = parse_all()
    print(f'\n📊 共 {len(all_scores)} 个不同职位代码')
    
    print('\n🗄️  Step 2: 写入数据库...')
    import_scores_to_db(all_scores)
    
    print('\n📊 Step 3: 计算四维评分...')
    calc_all_scores()
    
    print(f'\n🎉 完成!')


if __name__ == '__main__':
    main()
