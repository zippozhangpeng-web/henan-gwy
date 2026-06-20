#!/usr/bin/env python3
"""
河南省考真实职位表数据导入工具
从 henan.gov.cn 下载历年职位表 Excel → 解析 → 入库
"""
import os, sys, re, sqlite3, requests, openpyxl, xlrd

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOAD_DIR = os.path.join(PROJECT_DIR, 'real_data')
DB_PATH = os.path.join(PROJECT_DIR, 'gwy_data.db')

YEAR_FILES = {
    2026: {'url':'https://xcoss.henan.gov.cn/typtfile/20260105/37274f6c016a48b4bcdc66e7f11464cf.xlsx','fn':'2026.xlsx','type':'xlsx','sheets':['省辖市以下','省直机关'],'cols':13,'start':3},
    2025: {'url':'https://oss.henan.gov.cn/typtfile/20250108/a72f250122da4d7e99e445cb55483074.xls','fn':'2025.xls','type':'xls','sheets':['省辖市以下','省直机关'],'cols':13,'start':3},
    2024: {'url':'https://oss.henan.gov.cn/typtfile/20240116/046f9d69c3b84434a5dce577491f3447.xls','fn':'2024.xls','type':'xls','sheets':['省辖市以下','省直机关'],'cols':13,'start':3},
    2023: {'url':'https://oss.henan.gov.cn/typtfile/20230105/0b92bcc83e7344188f9706079320a4b5.xls','fn':'2023.xls','type':'xls','sheets':['省辖市以下','省直机关'],'cols':12,'start':3},
    2022: {'url':'https://oss.henan.gov.cn/typtfile/20220211/08bdae4b08694ba296359a47db47fefb.xls','fn':'2022.xls','type':'xls','sheets':['省直机关','省辖市以下'],'cols':10,'start':4},
}
HEADERS = {'User-Agent':'Mozilla/5.0'}
# 县区→地市
CTY = {
    '巩义':'郑州','新密':'郑州','新郑':'郑州','登封':'郑州','荥阳':'郑州','中牟':'郑州',
    '偃师':'洛阳','孟津':'洛阳','新安':'洛阳','栾川':'洛阳','嵩县':'洛阳','汝阳':'洛阳','宜阳':'洛阳','洛宁':'洛阳','伊川':'洛阳',
    '宛城':'南阳','卧龙':'南阳','南召':'南阳','方城':'南阳','西峡':'南阳','镇平':'南阳','内乡':'南阳','淅川':'南阳','社旗':'南阳','唐河':'南阳','新野':'南阳','桐柏':'南阳','邓州':'南阳',
    '魏都':'许昌','建安':'许昌','鄢陵':'许昌','襄城':'许昌','禹州':'许昌','长葛':'许昌',
    '川汇':'周口','淮阳':'周口','扶沟':'周口','西华':'周口','商水':'周口','沈丘':'周口','郸城':'周口','太康':'周口','鹿邑':'周口','项城':'周口',
    '红旗':'新乡','卫滨':'新乡','凤泉':'新乡','牧野':'新乡','新乡县':'新乡','获嘉':'新乡','原阳':'新乡','延津':'新乡','封丘':'新乡','卫辉':'新乡','辉县':'新乡','长垣':'新乡',
    '驿城':'驻马店','西平':'驻马店','上蔡':'驻马店','平舆':'驻马店','正阳':'驻马店','确山':'驻马店','泌阳':'驻马店','汝南':'驻马店','遂平':'驻马店','新蔡':'驻马店',
    '梁园':'商丘','睢阳':'商丘','民权':'商丘','睢县':'商丘','宁陵':'商丘','柘城':'商丘','虞城':'商丘','夏邑':'商丘','永城':'商丘',
    '浉河':'信阳','平桥':'信阳','罗山':'信阳','光山':'信阳','新县':'信阳','商城':'信阳','固始':'信阳','潢川':'信阳','淮滨':'信阳','息县':'信阳',
    '新华':'平顶山','卫东':'平顶山','石龙':'平顶山','湛河':'平顶山','宝丰':'平顶山','叶县':'平顶山','鲁山':'平顶山','郏县':'平顶山','舞钢':'平顶山','汝州':'平顶山',
    '龙亭':'开封','顺河':'开封','鼓楼':'开封','禹王台':'开封','祥符':'开封','杞县':'开封','通许':'开封','尉氏':'开封','兰考':'开封',
    '文峰':'安阳','北关':'安阳','殷都':'安阳','龙安':'安阳','安阳县':'安阳','汤阴':'安阳','滑县':'安阳','内黄':'安阳','林州':'安阳',
    '解放':'焦作','中站':'焦作','马村':'焦作','山阳':'焦作','修武':'焦作','博爱':'焦作','武陟':'焦作','温县':'焦作','沁阳':'焦作','孟州':'焦作',
    '华龙':'濮阳','清丰':'濮阳','南乐':'濮阳','范县':'濮阳','台前':'濮阳','濮阳县':'濮阳',
    '源汇':'漯河','郾城':'漯河','召陵':'漯河','舞阳':'漯河','临颍':'漯河',
    '湖滨':'三门峡','陕州':'三门峡','渑池':'三门峡','卢氏':'三门峡','义马':'三门峡','灵宝':'三门峡',
    '鹤山':'鹤壁','山城':'鹤壁','淇滨':'鹤壁','浚县':'鹤壁','淇县':'鹤壁',
    '济源':'济源',
}
CITIES = ['郑州','洛阳','南阳','许昌','周口','新乡','驻马店','商丘','信阳','平顶山','开封','安阳','焦作','濮阳','漯河','三门峡','鹤壁','济源']

def download():
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    r = {}
    for y, i in YEAR_FILES.items():
        fp = os.path.join(DOWNLOAD_DIR, i['fn'])
        if os.path.exists(fp) and os.path.getsize(fp) > 1000:
            print(f'  ✅ [{y}] 已存在'); r[y] = fp; continue
        print(f'  📥 [{y}] 下载中...')
        resp = requests.get(i['url'], headers=HEADERS, timeout=120, verify=False)
        if resp.status_code == 200:
            with open(fp,'wb') as f: f.write(resp.content)
            print(f'  ✅ [{y}] {len(resp.content)/1024/1024:.1f}MB')
            r[y] = fp
        else:
            print(f'  ❌ [{y}] HTTP {resp.status_code}')
    return r

def gv(s, r, c, xl):
    try:
        if xl:
            v = s.cell_value(r, c)
            return str(int(v)) if isinstance(v, float) and v == int(v) else str(v).strip()
        else:
            row = list(s.iter_rows(min_row=r+1, max_row=r+1, values_only=True))[0]
            v = row[c] if c < len(row) else ''
            if v is None: return ''
            return str(int(v)) if isinstance(v, float) and v == int(v) else str(v).strip()
    except: return ''

def parse_sheet(s, year, xl, nrows, ncols, start, label):
    cols2503 = {0:'u',1:'p',2:'c',3:'n',4:'e',5:'m',6:'a',7:'x',8:'o',9:'k'}
    cols2512 = {0:'u',1:'p',2:'c',3:'n',4:'a',5:'e',6:'x',7:'o',8:'m',11:'k'}
    cols2513 = {0:'u',1:'p',2:'c',3:'n',4:'a',5:'e',6:'d',7:'m',8:'x',9:'o',12:'k'}
    cm = cols2503 if year == 2022 else (cols2512 if year == 2023 else cols2513)
    recs, lu = [], ''
    if xl:
        for r in range(start, nrows):
            u = gv(s, r, 0, xl)
            p = gv(s, r, cm.get('p',1), xl)
            # 跳过真正的空行（unit和pos都为空），但保留合并单元格延续行（unit空但pos有值）
            if (not u and not p) or '招考职位由' in u or ('职位表' in u and '河南省' in u[:20]):
                continue
            if u: lu = u
            else: u = lu
            recs.append({
                'year':year, 'unit':u, 'pos':p,
                'code':gv(s,r,cm.get('c',2),xl), 'num':_i(gv(s,r,cm.get('n',3),xl)),
                'edu':gv(s,r,cm.get('e',5),xl), 'deg':gv(s,r,cm.get('d',0),xl) if 'd' in cm else '',
                'maj':gv(s,r,cm.get('m',7),xl), 'exp':gv(s,r,cm.get('x',8),xl),
                'oth':gv(s,r,cm.get('o',9),xl), 'note':gv(s,r,cm.get('k',12),xl),
            })
    else:
        for r_idx, row in enumerate(s.iter_rows(min_row=start+1, values_only=True)):
            if r_idx >= nrows: break
            row_tuple = list(row)
            u = str(row_tuple[0]).strip() if row_tuple[0] else ''
            def _g(idx):
                v = row_tuple[idx] if idx < len(row_tuple) else ''
                if v is None: return ''
                return str(int(v)) if isinstance(v, float) and v == int(v) else str(v).strip()
            p = _g(cm.get('p',1))
            if (not u and not p) or '招考职位由' in u or ('职位表' in u and '河南省' in u[:20]):
                continue
            if u: lu = u
            else: u = lu
            recs.append({
                'year':year, 'unit':u, 'pos':p,
                'code':_g(cm.get('c',2)), 'num':_i(_g(cm.get('n',3))),
                'edu':_g(cm.get('e',5)),
                'deg':_g(cm.get('d',0)) if 'd' in cm else '',
                'maj':_g(cm.get('m',7)), 'exp':_g(cm.get('x',8)),
                'oth':_g(cm.get('o',9)), 'note':_g(cm.get('k',12)),
            })
    return recs

def _i(v):
    try: return int(float(v.replace(',','')))
    except: return 0

def _city(u):
    if not u: return '其他'
    if u[:2] == '省' or '河南省' in u[:4]: return '省直'
    for cty, city in CTY.items():
        if cty in u: return city
    if '郑州' in u: return '郑州'
    for c in CITIES:
        if c in u: return c
    return '其他'

def _sys(u, p):
    if '公安' in u or '警察' in p: return '公安系统'
    if '法院' in u or '法官' in p: return '法院系统'
    if '检察' in u or '检察官' in p: return '检察院系统'
    if '纪委' in u or '监委' in u: return '纪委监委'
    if '司法' in u or '监狱' in u: return '司法行政'
    if any(k in u for k in ['省委','组织部','宣传部','统战部','政法委']): return '党委系统'
    if '发展改革' in u: return '发改系统'
    if '财政' in u: return '财政系统'
    if '审计' in u: return '审计系统'
    if '统计' in u: return '统计系统'
    if '市场监督' in u: return '市场监管系统'
    if '教育' in u and '体育' not in u: return '教育系统'
    if '卫生健康' in u or '卫健委' in u or ('卫生' in u and '爱卫' not in u): return '卫健系统'
    if '住建' in u or '住房' in u: return '住建系统'
    if '交通' in u or '运输' in u: return '交通系统'
    if '农业农村' in u: return '农业农村系统'
    if '人社' in u or '人力资源' in u: return '人社系统'
    if '民政' in u: return '民政系统'
    if '生态' in u or '环境' in u: return '生态环境系统'
    if '自然' in u or '规划' in u: return '自然资源系统'
    if '水利' in u: return '水利系统'
    if '退役' in u: return '退役军人系统'
    if '应急' in u: return '应急管理系统'
    if '信访' in u: return '信访系统'
    if '商务' in u: return '商务系统'
    if '科技' in u or '科学' in u: return '科技系统'
    if '工信' in u or '工业' in u: return '工信系统'
    if '文旅' in u or ('文化' in u and '宗教' not in u) or '旅游' in u or '体育' in u: return '文旅体育系统'
    if '林业' in u or '林' in u[-2:] or '园林' in u: return '林业系统'
    if '粮食' in u or '储备' in u: return '粮食储备系统'
    if '医保' in u or '"医保' in u: return '医疗保障系统'
    if '民族' in u or '宗教' in u: return '民族宗教系统'
    if '能源' in u or '煤矿' in u: return '能源系统'
    # 乡镇街道按尾部判断
    cu = u.replace('市','').replace('区','').replace('县','')
    if '乡镇' in u or '街道' in u or cu.endswith('乡') or cu.endswith('镇'):
        return '乡镇街道'
    if '人民政府' in u or '政府办公室' in u or '办公厅' in u or '管委会' in u or '办事处' in u:
        return '政府办公室'
    return '政府办公室'

def import_db(recs):
    conn = sqlite3.connect(DB_PATH); c = conn.cursor()
    for t in ['positions','position_scores','search_history']: c.execute(f'DROP TABLE IF EXISTS {t}')
    c.execute('''CREATE TABLE positions (id INTEGER PRIMARY KEY AUTOINCREMENT, year INTEGER NOT NULL,
        unit TEXT NOT NULL, position_name TEXT NOT NULL, position_code TEXT, recruit_num INTEGER,
        major_requirement TEXT, education TEXT, degree TEXT, political_status TEXT,
        experience_requirement TEXT, other_conditions TEXT, notes TEXT, exam_category TEXT,
        interview_ratio TEXT, city TEXT, district TEXT, system_type TEXT,
        min_score REAL, max_score REAL, avg_score REAL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    c.execute('''CREATE TABLE position_scores (position_id INTEGER PRIMARY KEY, difficulty_score REAL,
        difficulty_detail TEXT, region_score REAL, region_detail TEXT, salary_score REAL,
        salary_detail TEXT, prospect_score REAL, prospect_detail TEXT, overall_score REAL)''')
    c.execute('''CREATE TABLE search_history (id INTEGER PRIMARY KEY AUTOINCREMENT, major TEXT,
        education TEXT, city TEXT, political TEXT, experience TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    entries = []
    for r in recs:
        city = _city(r['unit'])
        st = _sys(r['unit'], r['pos'])
        political = '中共党员' if '中共党员' in r.get('oth','') else ''
        entries.append((r['year'],r['unit'],r['pos'],r['code'],r['num'],r['maj'],r['edu'],r['deg'],
            political,r['exp'],r['oth'],r['note'],'','',city,'',st,None,None,None))
    c.executemany('''INSERT INTO positions (year,unit,position_name,position_code,recruit_num,
        major_requirement,education,degree,political_status,experience_requirement,
        other_conditions,notes,exam_category,interview_ratio,city,district,system_type,
        min_score,max_score,avg_score) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', entries)
    conn.commit()
    c.execute('SELECT COUNT(*) FROM positions'); t = c.fetchone()[0]
    print(f'\n✅ 导入完成! 总岗位数: {t}')
    for y, cnt, rn in c.execute('SELECT year,COUNT(*),SUM(recruit_num) FROM positions GROUP BY year ORDER BY year'):
        print(f'   {y}年: {cnt} 条 / {int(rn)} 人')
    conn.close()

def main():
    import urllib3; urllib3.disable_warnings()
    print('='*60+'\n🏛️  河南省考职位表数据导入\n'+'='*60)
    dl = download()
    if not dl: print('❌ 下载失败'); sys.exit(1)
    all_r = []
    for year in sorted(YEAR_FILES):
        if year not in dl: continue
        info = YEAR_FILES[year]; fp = dl[year]
        print(f'\n📅 [{year}]...')
        try:
            if info['type'] == 'xlsx':
                wb = openpyxl.load_workbook(fp, read_only=True, data_only=True)
                for sn in info['sheets']:
                    if sn not in wb.sheetnames: continue
                    s = wb[sn]
                    # openpyxl read_only 需要传一个比实际行数大的值，内部用 enumerate 控制
                    recs = parse_sheet(s, year, False, 99999, info['cols'], info['start'], sn)
                    print(f'  [{sn}] {len(recs)} 条')
                    all_r.extend(recs)
                wb.close()
            else:
                wb = xlrd.open_workbook(fp)
                for sn in info['sheets']:
                    if sn not in wb.sheet_names(): continue
                    s = wb.sheet_by_name(sn)
                    recs = parse_sheet(s, year, True, s.nrows, s.ncols, info['start'], sn)
                    print(f'  [{sn}] {len(recs)} 条')
                    all_r.extend(recs)
        except Exception as e:
            print(f'  ❌ {e}'); import traceback; traceback.print_exc()
    print(f'\n📊 共 {len(all_r)} 条')
    if all_r: import_db(all_r); print(f'\n🎉 完成! DB: {DB_PATH}')
    else: print('无数据')

if __name__ == '__main__':
    main()
