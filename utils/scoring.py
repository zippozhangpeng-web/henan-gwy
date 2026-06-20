#!/usr/bin/env python3
"""
四维评分算法模块
基于岗位数据计算：上岸难度、地区优劣、薪酬待遇、发展前景
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'gwy_data.db')

# 河南18地市基础数据
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

SYSTEM_WEIGHTS = {
    '公安系统': {'salary': 1.2, 'prospect': 1.1},
    '法院系统': {'salary': 1.15, 'prospect': 1.1},
    '检察院系统': {'salary': 1.15, 'prospect': 1.05},
    '纪委监委': {'prospect': 1.3},
    '党委系统': {'prospect': 1.35},
    '政府办公室': {'prospect': 1.25},
    '发改委': {'prospect': 1.3},
    '财政局': {'salary': 1.05, 'prospect': 1.2},
    '组织部': {'prospect': 1.35},
    '宣传部': {'prospect': 1.15},
    '乡镇街道': {'prospect': 0.7},
}


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def calculate_difficulty(position):
    """上岸难易程度 (1-10)"""
    score = 5.0
    city = position.get('city', '郑州')
    recruit_num = position.get('recruit_num') or 1
    min_score = position.get('min_score') or 60
    education = position.get('education', '本科及以上')
    political = position.get('political_status', '不限')

    # 基于城市竞争力
    if city == '郑州':
        score += 2.0
    elif city in ['洛阳','南阳','新乡']:
        score += 1.0

    # 基于招录人数
    if recruit_num == 1:
        score += 1.5
    elif recruit_num == 2:
        score += 0.5
    elif recruit_num >= 5:
        score -= 1.0

    # 基于进面分数
    if min_score > 68:
        score += 2.0
    elif min_score > 63:
        score += 1.0
    elif min_score < 55:
        score -= 1.0

    # 学历要求
    if '硕士' in education:
        score -= 0.5
    elif '大专' in education:
        score += 1.0

    # 党员限制
    if political != '不限':
        score -= 0.5

    return round(max(1, min(10, score)), 1)


def calculate_region(position):
    """地区优劣 (1-10)"""
    city = position.get('city', '郑州')
    data = CITY_DATA.get(city, CITY_DATA['郑州'])

    if city == '郑州':
        return 9.5
    elif city in ['洛阳','南阳']:
        return 8.0
    elif data['gdp_rank'] <= 6:
        return 7.0
    elif data['gdp_rank'] <= 10:
        return 6.0
    elif data['gdp_rank'] <= 14:
        return 5.5
    else:
        return 5.0


def calculate_salary(position):
    """薪酬待遇 (1-10)"""
    city = position.get('city', '郑州')
    sys_type = position.get('system_type', '')
    district = position.get('district', '')

    data = CITY_DATA.get(city, CITY_DATA['郑州'])
    salary = data['avg_salary'] / 1000

    # 系统加成
    if '公安' in sys_type:
        salary += 0.8
    elif '法院' in sys_type or '检察' in sys_type:
        salary += 0.7
    elif sys_type in ['纪委监委','财政局','发改委']:
        salary += 0.5

    # 层级加成
    if district == '省直':
        salary += 0.5
    elif district == '市直':
        salary += 0.3

    return round(max(1, min(10, salary)), 1)


def calculate_prospect(position):
    """发展前景 (1-10)"""
    sys_type = position.get('system_type', '')
    district = position.get('district', '')
    city = position.get('city', '郑州')

    base = 5.0

    # 部门权重
    if sys_type in ['党委系统','政府办公室','纪委监委','发改委','组织部','宣传部']:
        base = 8.5
    elif sys_type in ['公安系统','法院系统','检察院系统','财政局']:
        base = 7.5
    elif '乡镇' in sys_type:
        base = 4.0
    else:
        base = 6.0

    # 层级加成
    if district == '省直':
        base += 1.2
    elif district == '市直':
        base += 0.8
    else:
        base -= 0.5

    # 城市加成
    if city == '郑州':
        base += 0.5
    elif city == '洛阳':
        base += 0.3

    return round(max(1, min(10, base)), 1)


def get_score_detail(position):
    """获取完整四维评分详情"""
    difficulty = calculate_difficulty(position)
    region = calculate_region(position)
    salary = calculate_salary(position)
    prospect = calculate_prospect(position)
    overall = round((difficulty + region + salary + prospect) / 4, 1)

    city = position.get('city', '郑州')
    sys_type = position.get('system_type', '')
    district = position.get('district', '')
    min_score = position.get('min_score') or 0
    max_score = position.get('max_score') or 0
    avg_score = position.get('avg_score') or 0
    city_data = CITY_DATA.get(city, CITY_DATA['郑州'])

    # 难度分析
    if difficulty >= 8:
        diff_label = '🔴 困难'
        diff_desc = '竞争非常激烈，建议充分备考，关注同类岗位分散风险。'
    elif difficulty >= 6:
        diff_label = '🟡 中等'
        diff_desc = '有一定竞争压力，认真准备有望上岸。'
    else:
        diff_label = '🟢 容易'
        diff_desc = '难度相对较低，上岸机会较大，是性价比较高的选择。'

    difficulty_detail = (
        f"进面分数区间：{min_score}-{max_score}分（平均{avg_score}分）。"
        f"{diff_desc}"
    )

    # 地区分析
    region_detail = (
        f"{city}GDP排名全省第{city_data['gdp_rank']}位，"
        f"常住人口{city_data['population']}万，"
        f"平均房价约{city_data['house_price']}元/㎡。"
    )
    if city == '郑州':
        region_detail += "省会城市，教育资源全省最优，交通便利，医疗条件完善。"
    elif city_data['gdp_rank'] <= 6:
        region_detail += "区域中心城市，配套完善，生活便利，发展潜力较好。"
    else:
        region_detail += "城市规模适中，生活节奏较慢，房价友好。"

    # 薪酬分析
    est_annual = city_data['avg_salary'] * 12
    if '公安' in sys_type:
        est_annual *= 1.2
    elif '法院' in sys_type or '检察' in sys_type:
        est_annual *= 1.15

    salary_detail = (
        f"预估全年收入约{int(est_annual/10000)}-{int(est_annual*1.3/10000)}万"
        f"（含公积金约{int(city_data['avg_salary']*0.24/100)}万/月+年终奖）。"
    )

    # 前景分析
    if district == '省直':
        prospect_detail = "省级单位，平台起点高，职业天花板较高。"
    elif district == '市直':
        prospect_detail = f"{city}市级单位，发展空间良好。"
    else:
        prospect_detail = f"{city}区县/基层单位，"
    if sys_type in ['党委系统','政府办公室','纪委监委','发改委']:
        prospect_detail += "核心部门，接触面广，晋升通道畅通。"
    elif '乡镇' in sys_type:
        prospect_detail += "基层岗位，锻炼机会多，晋升需较长时间积累。"
    else:
        prospect_detail += "常规晋升路径，工作稳定性高。"

    return {
        'difficulty_score': difficulty,
        'difficulty_label': diff_label,
        'difficulty_detail': difficulty_detail,
        'region_score': region,
        'region_detail': region_detail,
        'salary_score': salary,
        'salary_detail': salary_detail,
        'prospect_score': prospect,
        'prospect_detail': prospect_detail,
        'overall_score': overall,
        'city_data': {
            'name': city,
            'gdp_rank': city_data['gdp_rank'],
            'gdp': city_data['gdp'],
            'avg_salary': city_data['avg_salary'],
            'house_price': city_data['house_price'],
            'population': city_data['population'],
        }
    }
