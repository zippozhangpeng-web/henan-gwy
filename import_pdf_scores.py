#!/usr/bin/env python3
"""
补充解析PDF格式的面试名单
"""
import os, sys, re, sqlite3, glob

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
SCORE_DIR = os.path.join(PROJECT_DIR, 'score_data', '2025河南省考进面名单汇总')
DB_PATH = os.path.join(PROJECT_DIR, 'gwy_data.db')

HEADER_WORDS = {'附件1','姓名','准考证号','报考单位','职位代码','行测','成绩','申论','公安','总成绩','名次','备注','备注说明','笔试总成绩'}


def parse_pdf(filepath):
    import fitz
    doc = fitz.open(filepath)
    lines = []
    for p in range(doc.page_count):
        lines.extend([l.strip() for l in doc[p].get_text().split('\n') if l.strip()])
    doc.close()
    data = [l for l in lines if l not in HEADER_WORDS]

    fname = os.path.basename(filepath)
    is_gat = '公安厅' in fname
    scores = {}

    if is_gat:
        # 省公安厅格式：code行, 然后(name, ticket, score)循环出现
        i, cur = 0, None
        while i < len(data):
            if re.match(r'^\d{8}$', data[i]):
                cur = data[i]; i += 1; continue
            if cur and i + 2 < len(data):
                try:
                    sv = float(data[i+2])
                    if 0 < sv < 100:
                        scores.setdefault(cur, []).append(sv)
                except: pass
                i += 3
            else:
                i += 1
    else:
        # 城市格式：每8行一组 (name, ticket, unit, code, xingce, shenlun, gongan, total)
        i = 0
        while i + 7 < len(data):
            code = data[i+3]
            total = data[i+7]
            if re.match(r'^\d{8}$', code):
                try:
                    sv = float(total)
                    if 0 < sv < 100:
                        scores.setdefault(code, []).append(sv)
                        i += 8; continue
                except: pass
            i += 1

    return scores


def main():
    print('=' * 60)
    print('PDF面试名单解析')
    print('=' * 60)

    if not os.path.exists(SCORE_DIR):
        print(f'目录不存在: {SCORE_DIR}')
        sys.exit(1)

    all_scores = {}
    for fp in sorted(glob.glob(os.path.join(SCORE_DIR, '*.pdf'))):
        fname = os.path.basename(fp)
        try:
            ss = parse_pdf(fp)
            if ss:
                print(f'  [{fname[:12]}] {len(ss)} 个职位')
                for k, v in ss.items():
                    all_scores.setdefault(k, []).extend(v)
            else:
                print(f'  [{fname[:12]}] 0 个职位')
        except Exception as e:
            print(f'  [{fname[:12]}] error: {e}')

    print(f'\n共 {len(all_scores)} 个不同职位代码')

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    updated = 0
    for code, sc_list in all_scores.items():
        mn = round(min(sc_list), 2)
        mx = round(max(sc_list), 2)
        av = round(sum(sc_list)/len(sc_list), 2)
        # 只更新尚无为空的岗位
        c.execute('''UPDATE positions SET min_score=COALESCE(min_score,?),
                     max_score=COALESCE(max_score,?),
                     avg_score=COALESCE(avg_score,?)
                     WHERE year=2025 AND position_code LIKE ? AND min_score IS NULL''',
                  (mn, mx, av, code[:6] + '%'))
        updated += c.rowcount

    conn.commit()
    c.execute('SELECT COUNT(*) FROM positions WHERE year=2025 AND min_score IS NOT NULL')
    scored = c.fetchone()[0]
    c.execute('SELECT COUNT(*) FROM positions WHERE year=2025')
    total = c.fetchone()[0]
    conn.close()

    print(f'更新 {updated} 条')
    print(f'覆盖率: {scored}/{total} ({scored*100/total:.1f}%)')


if __name__ == '__main__':
    main()
