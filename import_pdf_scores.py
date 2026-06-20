#!/usr/bin/env python3
"""
全格式PDF面试名单解析：三门峡/省公安厅/省监狱/省教育考试院 格式兼容
"""
import os, sys, re, sqlite3, glob

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
SCORE_DIR = os.path.join(PROJECT_DIR, 'score_data', '2025河南省考进面名单汇总')
DB_PATH = os.path.join(PROJECT_DIR, 'gwy_data.db')

HEADERS = {'附件1','姓名','准考证号','报考单位','职位代码','行测','成绩','申论','公安','总成绩',
           '名次','备注','备注说明','笔试总成绩','报考职位','招录人数面试确认编号','性别','招录机关',
           '行测成绩申论成绩笔试成绩'}


def parse_pdf(filepath):
    import fitz
    fname = os.path.basename(filepath)
    doc = fitz.open(filepath)
    lines = []
    for p in range(doc.page_count):
        lines.extend([l.strip() for l in doc[p].get_text().split('\n') if l.strip()])
    doc.close()

    data = [l for l in lines if l not in HEADERS]
    scores = {}

    # --- 省公安厅格式: code行 + (name,ticket,score)循环 ---
    if '公安厅' in fname:
        i, cur = 0, None
        while i < len(data):
            if re.match(r'^\d{8}$', data[i]):
                cur = data[i]; i += 1; continue
            if cur and i + 2 < len(data) and re.match(r'^\d+$', data[i+1]):
                try:
                    scores.setdefault(cur, []).append(float(data[i+2]))
                except: pass
                i += 3
            else: i += 1
        return scores

    # --- 三门峡格式: 每10行一组 ---
    if '三门峡' in fname:
        i = 0
        while i + 9 < len(data):
            pos_line = data[i+1]
            m = re.search(r'(\d{8})', pos_line)
            total = data[i+9]
            if m:
                try:
                    scores.setdefault(m.group(1), []).append(float(total))
                except: pass
            i += 10
        return scores

    # --- 省监狱格式: 每6行一组 ---
    if '监狱' in fname:
        i = 0
        while i + 5 < len(data):
            code_line = data[i+2]
            m = re.search(r'(\d{8})', code_line)
            total = data[i+5]
            if m:
                try:
                    scores.setdefault(m.group(1), []).append(float(total))
                except: pass
            i += 6
        return scores

    # --- 省教育考试院: 检查格式 ---
    if '教育考试' in fname:
        # 尝试每4行 (code, name, ticket, score) 或每8行
        i = 0
        while i + 3 < len(data):
            if re.match(r'^\d{8}$', data[i]) and re.match(r'^\d+\.?\d*$', data[i+3]):
                try:
                    scores.setdefault(data[i], []).append(float(data[i+3]))
                except: pass
                i += 4; continue
            i += 1
        if scores: return scores
        # fallback: 8行格式
        i = 0
        while i + 7 < len(data):
            code = data[i+3]
            total = data[i+7]
            if re.match(r'^\d{8}$', code):
                try:
                    scores.setdefault(code, []).append(float(total))
                except: pass
                i += 8; continue
            i += 1
        return scores

    # --- 默认城市格式: 每8行一组 ---
    i = 0
    while i + 7 < len(data):
        code = data[i+3]
        total = data[i+7]
        if re.match(r'^\d{8}$', code):
            try:
                scores.setdefault(code, []).append(float(total))
            except: pass
            i += 8; continue
        i += 1
    return scores


def main():
    print('=' * 60)
    print('全格式PDF面试名单解析')
    print('=' * 60)

    all_scores = {}
    for fp in sorted(glob.glob(os.path.join(SCORE_DIR, '*.pdf'))):
        try:
            ss = parse_pdf(fp)
            fname = os.path.basename(fp)
            label = fname.split('.')[0][:12]
            if ss:
                print(f'  ✅ [{label}] {len(ss)} 个职位')
                for k, v in ss.items():
                    all_scores.setdefault(k, []).extend(v)
            else:
                print(f'  ⚠️  [{label}] 0 个职位')
        except Exception as e:
            print(f'  ❌ [{fname[:12]}] {e}')

    print(f'\n📊 共 {len(all_scores)} 个不同职位代码')

    # 更新DB
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    updated = 0
    for code, sc_list in all_scores.items():
        if not sc_list: continue
        mn = round(min(sc_list), 2)
        mx = round(max(sc_list), 2)
        av = round(sum(sc_list)/len(sc_list), 2)
        # 用模糊匹配避免code尾号变化
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
    print(f'🎉 完成!')


if __name__ == '__main__':
    main()
