#!/usr/bin/env python3
"""
河南公考岗位演示数据生成器
生成 2000+ 条逼真的模拟数据
"""
import sqlite3
import random
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'gwy_data.db')

# ========== 河南省18个地市基础数据 ==========
CITIES = {
    '郑州': {
        'gdp_rank': 1, 'gdp': 14370, 'population': 1282, 'avg_salary': 8500,
        'house_price': 14000, 'is_capital': True, 'districts': ['市直','金水区','二七区','中原区','管城回族区','惠济区','上街区','巩义市','新密市','新郑市','登封市','荥阳市','中牟县']
    },
    '洛阳': {
        'gdp_rank': 2, 'gdp': 5820, 'population': 707, 'avg_salary': 6800,
        'house_price': 8500, 'districts': ['市直','涧西区','西工区','老城区','瀍河区','洛龙区','偃师区','孟津区','新安县','栾川县','嵩县','汝阳县','宜阳县','洛宁县','伊川县']
    },
    '南阳': {
        'gdp_rank': 3, 'gdp': 4710, 'population': 971, 'avg_salary': 5500,
        'house_price': 6500, 'districts': ['市直','宛城区','卧龙区','南召县','方城县','西峡县','镇平县','内乡县','淅川县','社旗县','唐河县','新野县','桐柏县','邓州市']
    },
    '许昌': {
        'gdp_rank': 4, 'gdp': 3530, 'population': 438, 'avg_salary': 6000,
        'house_price': 6200, 'districts': ['市直','魏都区','建安区','鄢陵县','襄城县','禹州市','长葛市']
    },
    '周口': {
        'gdp_rank': 5, 'gdp': 3500, 'population': 885, 'avg_salary': 5200,
        'house_price': 5500, 'districts': ['市直','川汇区','淮阳区','扶沟县','西华县','商水县','沈丘县','郸城县','太康县','鹿邑县','项城市']
    },
    '新乡': {
        'gdp_rank': 6, 'gdp': 3460, 'population': 625, 'avg_salary': 5800,
        'house_price': 7000, 'districts': ['市直','红旗区','卫滨区','凤泉区','牧野区','新乡县','获嘉县','原阳县','延津县','封丘县','卫辉市','辉县市','长垣市']
    },
    '驻马店': {
        'gdp_rank': 7, 'gdp': 3220, 'population': 700, 'avg_salary': 5000,
        'house_price': 5000, 'districts': ['市直','驿城区','西平县','上蔡县','平舆县','正阳县','确山县','泌阳县','汝南县','遂平县','新蔡县']
    },
    '商丘': {
        'gdp_rank': 8, 'gdp': 3100, 'population': 781, 'avg_salary': 5300,
        'house_price': 5800, 'districts': ['市直','梁园区','睢阳区','民权县','睢县','宁陵县','柘城县','虞城县','夏邑县','永城市']
    },
    '信阳': {
        'gdp_rank': 9, 'gdp': 3060, 'population': 623, 'avg_salary': 5100,
        'house_price': 5500, 'districts': ['市直','浉河区','平桥区','罗山县','光山县','新县','商城县','固始县','潢川县','淮滨县','息县']
    },
    '平顶山': {
        'gdp_rank': 10, 'gdp': 2820, 'population': 498, 'avg_salary': 5500,
        'house_price': 5800, 'districts': ['市直','新华区','卫东区','石龙区','湛河区','宝丰县','叶县','鲁山县','郏县','舞钢市','汝州市']
    },
    '开封': {
        'gdp_rank': 11, 'gdp': 2710, 'population': 457, 'avg_salary': 5600,
        'house_price': 6200, 'districts': ['市直','龙亭区','顺河回族区','鼓楼区','禹王台区','祥符区','杞县','通许县','尉氏县','兰考县']
    },
    '安阳': {
        'gdp_rank': 12, 'gdp': 2580, 'population': 548, 'avg_salary': 5400,
        'house_price': 5800, 'districts': ['市直','文峰区','北关区','殷都区','龙安区','安阳县','汤阴县','滑县','内黄县','林州市']
    },
    '焦作': {
        'gdp_rank': 13, 'gdp': 2310, 'population': 354, 'avg_salary': 5600,
        'house_price': 5500, 'districts': ['市直','解放区','中站区','马村区','山阳区','修武县','博爱县','武陟县','温县','沁阳市','孟州市']
    },
    '濮阳': {
        'gdp_rank': 14, 'gdp': 2040, 'population': 377, 'avg_salary': 5300,
        'house_price': 5500, 'districts': ['市直','华龙区','清丰县','南乐县','范县','台前县','濮阳县']
    },
    '漯河': {
        'gdp_rank': 15, 'gdp': 1880, 'population': 236, 'avg_salary': 5400,
        'house_price': 5200, 'districts': ['市直','源汇区','郾城区','召陵区','舞阳县','临颍县']
    },
    '三门峡': {
        'gdp_rank': 16, 'gdp': 1780, 'population': 227, 'avg_salary': 5600,
        'house_price': 5000, 'districts': ['市直','湖滨区','陕州区','渑池县','卢氏县','义马市','灵宝市']
    },
    '鹤壁': {
        'gdp_rank': 17, 'gdp': 1050, 'population': 157, 'avg_salary': 5200,
        'house_price': 4800, 'districts': ['市直','鹤山区','山城区','淇滨区','浚县','淇县']
    },
    '济源': {
        'gdp_rank': 18, 'gdp': 830, 'population': 73, 'avg_salary': 5500,
        'house_price': 5000, 'districts': ['市直']
    },
    '省直': {
        'gdp_rank': 0, 'gdp': 0, 'population': 0, 'avg_salary': 9500,
        'house_price': 14000, 'is_capital': True, 'is_province': True,
        'districts': ['省直'],
    },
}

SYSTEM_TYPES = ['公安系统','法院系统','检察院系统','司法行政','纪委监委','党委系统','政府办公室','发改委','财政局','教育局','卫健委','住建局','交通局','农业农村局','审计局','市场监管局','统计局','自然资源局','生态环境局','水利局','人社局','民政局','退役军人局','应急管理局','乡镇街道']

MAJORS = ['法学','法律','法学类','会计学','财务管理','计算机科学与技术','软件工程','汉语言文学','新闻学','经济学','金融学','工商管理','行政管理','公共管理','土木工程','建筑学','临床医学','药学','护理学','不限专业']

EDUCATIONS = ['大专及以上','本科及以上','硕士研究生及以上','仅限本科','仅限硕士研究生']

POLITICAL_OPTIONS = ['不限','中共党员','中共党员或共青团员']

EXPERIENCE_OPTIONS = ['不限','2年以上基层工作经历','1年以上基层工作经历']

EXAM_CATEGORIES = ['A类（省市机关）','B类（县乡机关）','C类（公安岗位）']

def random_major():
    if random.random() < 0.2:
        return '不限专业'
    n = random.randint(1, 3)
    return '、'.join(random.sample(MAJORS, n))

def gen_position_code(year, idx):
    return f"{year % 100}001{idx:04d}"

def assign_scores(city, system_type, education, recruit_num, political):
    """基于规则生成合理的四维评分"""
    # 上岸难度（越高越容易上岸，越低越难）
    base_diff = 5.0
    if city == '省直':
        base_diff -= 2.0  # 省级单位竞争最激烈，最难上岸
    elif city == '郑州':
        base_diff -= 1.5
    elif city in ['洛阳','南阳','新乡']:
        base_diff -= 0.5
    if recruit_num == 1:
        base_diff -= 1.5  # 只招1人，难度大
    elif recruit_num >= 3:
        base_diff += 1.0  # 招人多，机会大
    if '不限专业' != MAJORS[0]:  # 有限制专业反而竞争小（门槛高）
        base_diff += 0.5
    if '大专' in education:
        base_diff += 1.0  # 大专岗位竞争更激烈
    if political != '不限':
        base_diff -= 0.5
    difficulty = round(max(1, min(10, base_diff + random.uniform(-1, 1))), 2)

    # 地区优劣
    city_data = CITIES[city]
    region_base = 6.0
    if city == '省直':
        region_base = 9.5  # 省级机关位于郑州，享省会资源
    elif city == '郑州':
        region_base = 9.0
    elif city in ['洛阳','南阳']:
        region_base = 7.5
    elif city_data['gdp_rank'] <= 6:
        region_base = 7.0
    elif city_data['gdp_rank'] <= 12:
        region_base = 6.0
    else:
        region_base = 5.0
    region = round(max(1, min(10, region_base + random.uniform(-0.5, 0.5))), 2)

    # 薪酬待遇
    salary_base = city_data['avg_salary'] / 1000
    if system_type in ['公安系统','法院系统','检察院系统']:
        salary_base += 0.8  # 政法系统补贴
    elif system_type in ['财政局','发改委','纪委监委']:
        salary_base += 0.5
    if '市直' == '市直':
        salary_base += 0.3
    salary = round(max(1, min(10, salary_base + random.uniform(-0.5, 0.5))), 2)

    # 发展前景
    prospect_base = 5.0
    if system_type in ['党委系统','政府办公室','纪委监委','发改委','财政局']:
        prospect_base = 8.0
    elif system_type in ['公安系统','法院系统','检察院系统']:
        prospect_base = 7.5
    elif system_type in ['组织部','宣传部']:
        prospect_base = 8.5
    elif '乡镇' in system_type:
        prospect_base = 4.0
    if city == '郑州':
        prospect_base += 0.8
    elif city == '洛阳':
        prospect_base += 0.5
    prospect = round(max(1, min(10, prospect_base + random.uniform(-0.8, 0.8))), 2)

    # 综合评分（加权）
    overall = round(difficulty * 0.25 + region * 0.25 + salary * 0.25 + prospect * 0.25, 2)

    return {
        'difficulty': difficulty, 'region': region, 'salary': salary,
        'prospect': prospect, 'overall': overall
    }

def gen_score_range(difficulty):
    """根据难度生成进面分数范围"""
    base = 55 + (difficulty / 10) * 20  # 55-75 范围
    min_s = round(base - random.uniform(3, 8), 2)
    max_s = round(base + random.uniform(2, 5), 2)
    avg_s = round((min_s + max_s) / 2 + random.uniform(-1, 1), 2)
    return max(45, min_s), min(85, max_s), avg_s

def seed_database():
    """生成种子数据"""
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # 创表
    c.execute('''
        CREATE TABLE positions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            year INTEGER NOT NULL,
            unit TEXT NOT NULL,
            position_name TEXT NOT NULL,
            position_code TEXT,
            recruit_num INTEGER,
            major_requirement TEXT,
            education TEXT,
            degree TEXT,
            political_status TEXT,
            experience_requirement TEXT,
            other_conditions TEXT,
            notes TEXT,
            exam_category TEXT,
            interview_ratio TEXT,
            city TEXT,
            district TEXT,
            system_type TEXT,
            min_score REAL,
            max_score REAL,
            avg_score REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    c.execute('''
        CREATE TABLE position_scores (
            position_id INTEGER PRIMARY KEY,
            difficulty_score REAL,
            difficulty_detail TEXT,
            region_score REAL,
            region_detail TEXT,
            salary_score REAL,
            salary_detail TEXT,
            prospect_score REAL,
            prospect_detail TEXT,
            overall_score REAL
        )
    ''')

    c.execute('''
        CREATE TABLE search_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            major TEXT,
            education TEXT,
            city TEXT,
            political TEXT,
            experience TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 单位名称池
    provincial_units = [
        '中共河南省委办公厅', '中共河南省委组织部', '中共河南省委宣传部',
        '中共河南省委统战部', '中共河南省委政法委',
        '河南省人民政府办公厅', '河南省发展和改革委员会', '河南省教育厅',
        '河南省科学技术厅', '河南省工业和信息化厅', '河南省公安厅',
        '河南省民政厅', '河南省司法厅', '河南省财政厅',
        '河南省人力资源和社会保障厅', '河南省自然资源厅', '河南省生态环境厅',
        '河南省住房和城乡建设厅', '河南省交通运输厅', '河南省水利厅',
        '河南省农业农村厅', '河南省商务厅', '河南省文化和旅游厅',
        '河南省卫生健康委员会', '河南省退役军人事务厅', '河南省应急管理厅',
        '河南省审计厅', '河南省市场监督管理局', '河南省统计局',
        '河南省高级人民法院', '河南省人民检察院', '河南省纪委监委',
        '河南省信访局', '河南省粮食和物资储备局', '河南省医疗保障局',
        '河南省机关事务管理局', '河南省体育局', '河南省药品监督管理局',
    ]

    city_units_templates = {
        '公安局': '{}市公安局', '法院': '{}市中级人民法院',
        '检察院': '{}市人民检察院', '纪委监委': '{}市纪委监委',
        '发改委': '{}市发展和改革委员会', '财政局': '{}市财政局',
        '教育局': '{}市教育局', '卫健委': '{}市卫生健康委员会',
        '住建局': '{}市住房和城乡建设局', '交通局': '{}市交通运输局',
        '审计局': '{}市审计局', '市场监管局': '{}市市场监督管理局',
        '司法局': '{}市司法局', '民政局': '{}市民政局',
        '人社局': '{}市人力资源和社会保障局', '水利局': '{}市水利局',
        '农业农村局': '{}市农业农村局', '自然资源局': '{}市自然资源和规划局',
        '生态环境局': '{}市生态环境局', '统计局': '{}市统计局',
    }

    entries = []
    pos_id = 0
    years = [2022, 2023, 2024, 2025, 2026]

    for year in years:
        # === 省级单位（独立生成，不循环城市）===
        for pu in provincial_units:
            if random.random() < 0.75:  # 75%概率生成省直岗位
                pos_id += 1
                sys_type = '党委系统' if '省委' in pu or '纪委' in pu else \
                           '法院系统' if '法院' in pu else \
                           '检察院系统' if '检察' in pu else \
                           '公安系统' if '公安' in pu else '政府办公室'
                if '办公厅' in pu or '办公室' in pu:
                    sys_type = '政府办公室'
                entries.append(build_entry(year, '省直', '省直', pu, sys_type, pos_id))

        # === 各地市（含市直+区县）===
        for city_name, city_data in CITIES.items():
            if city_name == '省直':
                continue  # 省直已单独生成

            # 市直单位
            for unit_key, unit_template in city_units_templates.items():
                if random.random() < 0.25:
                    continue
                pos_id += 1
                unit_name = unit_template.format(city_name)
                sys_map = {
                    '公安局': '公安系统', '法院': '法院系统', '检察院': '检察院系统',
                    '纪委监委': '纪委监委', '司法局': '司法行政',
                }
                sys_type = sys_map.get(unit_key, '政府办公室')
                if unit_key in ['发改委','财政局','审计局','市场监管局','统计局']:
                    sys_type = unit_key.replace('局','')
                entries.append(build_entry(year, city_name, '市直', unit_name, sys_type, pos_id))

            # 区县单位
            num_district = min(len(city_data['districts']), random.randint(2, 5))
            selected_districts = random.sample(city_data['districts'], num_district)
            for district in selected_districts:
                if district == '市直':
                    continue
                # 区县公安/法院/检察/乡镇
                for st in ['公安系统','法院系统','检察院系统','乡镇街道']:
                    if random.random() < 0.5:
                        continue
                    pos_id += 1
                    if st == '公安系统':
                        unit_name = f'{city_name}市公安局{district}分局'
                    elif st == '法院系统':
                        unit_name = f'{city_name}市{district}区人民法院' if '区' in district else f'{district}县人民法院'
                    elif st == '检察院系统':
                        unit_name = f'{city_name}市{district}区人民检察院' if '区' in district else f'{district}县人民检察院'
                    else:
                        village = random.choice(['城关','龙泉','花园','朝阳','建设','人民','新华','红旗'])
                        unit_name = f'{city_name}市{district}街道办事处' if '区' in district else f'{district}县{village}乡人民政府'
                    entries.append(build_entry(year, city_name, district, unit_name, st, pos_id))

    # 打乱顺序使数据更真实
    random.shuffle(entries)

    # 批量插入
    c.executemany('''
        INSERT INTO positions (year, unit, position_name, position_code, recruit_num,
            major_requirement, education, degree, political_status, experience_requirement,
            other_conditions, notes, exam_category, interview_ratio, city, district,
            system_type, min_score, max_score, avg_score)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', entries)

    # 评分数据
    for i, entry in enumerate(entries):
        year, _, _, _, _, _, edu, _, political, _, _, _, _, _, city, district, sys_type, min_s, max_s, avg_s = entry[:21]
        city_data = CITIES.get(city, CITIES['郑州'])
        scores = assign_scores(city, sys_type, edu, random.randint(1,5), political)

        difficulty_detail = f"进面最低分{min_s}分，最高分{max_s}分，平均分{avg_s}分。"
        if scores['difficulty'] >= 7:
            difficulty_detail += f"该岗位门槛适中，相对容易上岸。"
        elif scores['difficulty'] >= 5:
            difficulty_detail += f"难度中等，有一定竞争压力。"
        else:
            difficulty_detail += f"竞争激烈，该岗位位于{city}，建议充分备考。"

        region_detail = f"{city}GDP排名全省第{city_data['gdp_rank']}位，"
        if city == '郑州':
            region_detail += "省会城市，交通便利，教育资源丰富，医疗条件优越。"
        elif city_data['gdp_rank'] <= 6:
            region_detail += "区域中心城市，配套完善，生活便利。"
        else:
            region_detail += "生活节奏适中，房价友好，环境宜居。"

        salary_base = city_data['avg_salary']
        salary_detail = f"预估年薪{int(salary_base * 12 / 10000)}-{int(salary_base * 16 / 10000)}万（含公积金、年终奖），"
        if sys_type in ['公安系统','法院系统','检察院系统']:
            salary_detail += "政法系统有专项津贴，公积金缴存比例较高。"
        else:
            salary_detail += "享受公务员标准待遇，五险一金齐全。"

        prospect_detail = "省级单位" if district == '省直' else \
                          f"{city}市级单位，发展空间" if district == '市直' else \
                          f"{city}{district}基层单位，"
        if sys_type in ['党委系统','政府办公室','纪委监委','发改委','财政局']:
            prospect_detail += "核心部门，晋升通道畅通。"
        elif '乡镇' in sys_type:
            prospect_detail += "基层岗位，锻炼机会多，晋升需积累。"
        else:
            prospect_detail += "常规晋升路径，稳定可靠。"

        c.execute('''
            INSERT INTO position_scores (position_id, difficulty_score, difficulty_detail,
                region_score, region_detail, salary_score, salary_detail,
                prospect_score, prospect_detail, overall_score)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (i+1, scores['difficulty'], difficulty_detail, scores['region'], region_detail,
              scores['salary'], salary_detail, scores['prospect'], prospect_detail, scores['overall']))

    conn.commit()

    # 统计
    c.execute('SELECT COUNT(*) FROM positions')
    total = c.fetchone()[0]
    c.execute('SELECT year, COUNT(*) FROM positions GROUP BY year ORDER BY year')
    by_year = c.fetchall()

    print(f'✅ 数据库生成成功: {DB_PATH}')
    print(f'📊 总岗位数: {total}')
    print(f'📅 按年份分布:')
    for y, cnt in by_year:
        print(f'   {y}年: {cnt} 条')
    conn.close()


def build_entry(year, city, district, unit_name, sys_type, pos_id):
    recruit_num = random.choices([1,2,3,4,5,6,8,10], weights=[30,20,15,10,8,7,5,5])[0]
    major_req = random_major()
    education = random.choices(EDUCATIONS, weights=[10,60,15,10,5])[0]
    degree = '学士及以上' if '本科' in education else '硕士及以上' if '硕士' in education else '不限'
    political = random.choices(POLITICAL_OPTIONS, weights=[60,30,10])[0]
    experience = random.choices(EXPERIENCE_OPTIONS, weights=[75,20,5])[0]
    exam_cat = 'A类（省市机关）' if district in ['省直','市直'] else \
               'C类（公安岗位）' if sys_type == '公安系统' else 'B类（县乡机关）'
    interview_ratio = '1:3'

    position_names = [
        f'一级科员', f'一级科员', f'一级科员',
        f'执法勤务类一级警长以下', f'警务技术类一级警长以下',
        f'五级法官助理', f'五级检察官助理',
        f'四级主任科员以下', f'二级主任科员以下',
    ]
    position_name = random.choice(position_names)
    if sys_type == '公安系统' and '科员' in position_name:
        position_name = random.choice(['执法勤务类一级警长以下', '警务技术类一级警长以下'])
    elif sys_type == '法院系统' and '科员' in position_name:
        position_name = '五级法官助理'
    elif sys_type == '检察院系统' and '科员' in position_name:
        position_name = '五级检察官助理'

    code = gen_position_code(year, pos_id)

    other_conditions = ''
    if random.random() < 0.15:
        other_conditions = random.choice([
            '限应届毕业生报考', '限男性', '限女性', '需取得法律职业资格A证',
            '需具有2年以上相关工作经验',
        ])

    notes = ''
    if sys_type == '公安系统':
        notes = random.choices(['需进行体能测评','需进行体能测评和心理素质测评'], weights=[70,30])[0]
    elif random.random() < 0.2:
        notes = random.choice([
            '经常出差，适合男性', '需24小时值班', '工作强度较大',
            '需长期驻外工作', '适合计算机相关专业',
        ])

    scores = assign_scores(city, sys_type, education, recruit_num, political)
    min_s, max_s, avg_s = gen_score_range(scores['difficulty'])

    return (
        year, unit_name, position_name, code, recruit_num,
        major_req, education, degree, political, experience,
        other_conditions, notes, exam_cat, interview_ratio,
        city, district, sys_type, min_s, max_s, avg_s
    )


if __name__ == '__main__':
    seed_database()
