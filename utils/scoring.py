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

    # 基于进面分数（高分→难上岸→减分，低分→易上岸→加分）
    if min_score > 68:
        score -= 2.0
    elif min_score > 63:
        score -= 1.0
    elif min_score < 55:
        score += 1.0

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
    """获取完整四维评分详情，包含评分因子明细"""
    difficulty = calculate_difficulty(position)
    region = calculate_region(position)
    salary = calculate_salary(position)
    prospect = calculate_prospect(position)
    overall = round((difficulty + region + salary + prospect) / 4, 1)

    city = position.get('city', '郑州')
    sys_type = position.get('system_type', '')
    district = position.get('district', '')
    education = position.get('education', '本科及以上')
    political = position.get('political_status', '不限')
    recruit_num = position.get('recruit_num') or 1
    min_score = position.get('min_score') or 0
    max_score = position.get('max_score') or 0
    avg_score = position.get('avg_score') or 0
    city_data = CITY_DATA.get(city, CITY_DATA['郑州'])

    # ========================================
    # 上岸难度 — 评分因子
    # ========================================
    difficulty_rule = "基准线5.0，城市竞争力强→加分(竞争大但岗位好)，招录人数少→减分(难上岸)，进面分高→减分(越难上岸)，学历门槛高→加分(竞争小)，政治面貌有限制→加分(竞争小)"

    diff_factors = []
    diff_sum = 5.0
    diff_factors.append({'name': '基础分（基准线）', 'value': '5.0', 'impact': '+5.0'})

    # 城市因子
    if city == '郑州':
        diff_factors.append({'name': '城市竞争力', 'value': f'{city}是省会城市', 'impact': '+2.0'})
        diff_sum += 2.0
    elif city in ['洛阳', '南阳', '新乡']:
        diff_factors.append({'name': '城市竞争力', 'value': f'{city}为区域中心城市', 'impact': '+1.0'})
        diff_sum += 1.0
    else:
        diff_factors.append({'name': '城市竞争力', 'value': f'{city}', 'impact': '+0.0'})

    # 招录人数因子
    if recruit_num == 1:
        diff_factors.append({'name': '招录人数', 'value': f'仅招{recruit_num}人', 'impact': '+1.5'})
        diff_sum += 1.5
    elif recruit_num == 2:
        diff_factors.append({'name': '招录人数', 'value': f'招{recruit_num}人', 'impact': '+0.5'})
        diff_sum += 0.5
    elif recruit_num >= 5:
        diff_factors.append({'name': '招录人数', 'value': f'招{recruit_num}人（较多）', 'impact': '-1.0'})
        diff_sum -= 1.0
    else:
        diff_factors.append({'name': '招录人数', 'value': f'招{recruit_num}人', 'impact': '+0.0'})

    # 进面分数因子
    if min_score and min_score > 0:
        if min_score > 68:
            diff_factors.append({'name': '进面分数', 'value': f'最低{min_score}分（高分段）', 'impact': '-2.0'})
            diff_sum -= 2.0
        elif min_score > 63:
            diff_factors.append({'name': '进面分数', 'value': f'最低{min_score}分（中高分段）', 'impact': '-1.0'})
            diff_sum -= 1.0
        elif min_score < 55:
            diff_factors.append({'name': '进面分数', 'value': f'最低{min_score}分（偏低）', 'impact': '+1.0'})
            diff_sum += 1.0
        else:
            diff_factors.append({'name': '进面分数', 'value': f'最低{min_score}分', 'impact': '+0.0'})
    else:
        diff_factors.append({'name': '进面分数', 'value': '暂无数据', 'impact': '+0.0'})

    # 学历因子
    if '硕士' in education:
        diff_factors.append({'name': '学历要求', 'value': education, 'impact': '-0.5'})
        diff_sum -= 0.5
    elif '大专' in education:
        diff_factors.append({'name': '学历要求', 'value': education, 'impact': '+1.0'})
        diff_sum += 1.0
    else:
        diff_factors.append({'name': '学历要求', 'value': education, 'impact': '+0.0'})

    # 政治面貌因子
    if political != '不限':
        diff_factors.append({'name': '政治面貌', 'value': political, 'impact': '-0.5'})
        diff_sum -= 0.5
    else:
        diff_factors.append({'name': '政治面貌', 'value': '不限', 'impact': '+0.0'})

    # 截断说明
    if diff_sum > 10:
        diff_factors.append({'name': '截断调整', 'value': f'原始合计{diff_sum:.1f}，截断至10', 'impact': f'-{diff_sum - 10:.1f}'})
    diff_factors.append({'name': '最终得分', 'value': f'{difficulty}', 'impact': ''})

    # ========================================
    # 地区优劣 — 评分因子
    # ========================================
    region_rule = "基于城市GDP排名确定基础分（省会9.5→区域中心8.0→第3-6名7.0→第7-10名6.0→第11-14名5.5→其他5.0）"

    region_factors = []
    region_factors.append({
        'name': 'GDP排名',
        'value': f'全省第{city_data["gdp_rank"]}位（GDP {city_data["gdp"]}亿）',
        'impact': '-'
    })
    region_factors.append({
        'name': '人均薪资',
        'value': f'{city_data["avg_salary"]}元/月',
        'impact': '-'
    })
    region_factors.append({
        'name': '房价水平',
        'value': f'{city_data["house_price"]}元/㎡',
        'impact': '-'
    })
    is_capital = city_data.get('is_capital', False)
    region_factors.append({
        'name': '是否为省会',
        'value': '是' if is_capital else '否',
        'impact': '+' if is_capital else '-'
    })
    region_factors.append({
        'name': '最终得分',
        'value': f'{region}',
        'impact': ''
    })

    # ========================================
    # 薪酬待遇 — 评分因子
    # ========================================
    salary_rule = "城市平均薪资(千元)为底分 + 系统加成(公安+0.8/法检+0.7/核心+0.5) + 层级加成(省直+0.5/市直+0.3)，满分截断至10"

    base_salary = city_data['avg_salary'] / 1000
    salary_factors = []
    salary_factors.append({
        'name': '城市平均薪资',
        'value': f'{city_data["avg_salary"]}元/月',
        'impact': f'{base_salary:.1f}'
    })

    sys_bonus = 0.0
    if '公安' in sys_type:
        sys_bonus = 0.8
        salary_factors.append({'name': '系统加成', 'value': '公安系统津贴', 'impact': '+0.8'})
    elif '法院' in sys_type or '检察' in sys_type:
        sys_bonus = 0.7
        salary_factors.append({'name': '系统加成', 'value': '法检系统津贴', 'impact': '+0.7'})
    elif sys_type in ['纪委监委', '财政局', '发改委']:
        sys_bonus = 0.5
        salary_factors.append({'name': '系统加成', 'value': f'{sys_type}津贴', 'impact': '+0.5'})
    else:
        salary_factors.append({'name': '系统加成', 'value': sys_type or '无', 'impact': '+0.0'})

    district_bonus = 0.0
    if district == '省直':
        district_bonus = 0.5
        salary_factors.append({'name': '层级加成', 'value': '省直机关', 'impact': '+0.5'})
    elif district == '市直':
        district_bonus = 0.3
        salary_factors.append({'name': '层级加成', 'value': '市直机关', 'impact': '+0.3'})
    else:
        salary_factors.append({'name': '层级加成', 'value': district or '县级', 'impact': '+0.0'})

    salary_factors.append({'name': '最终得分', 'value': f'{salary}', 'impact': ''})

    # ========================================
    # 发展前景 — 评分因子
    # ========================================
    prospect_rule = "系统类型确定基础分(核心部门8.5→政法7.5→乡镇4.0→其他6.0) + 层级加成(省直+1.2/市直+0.8/县级-0.5) + 城市加成(郑州+0.5/洛阳+0.3)"

    # 确定 base
    if sys_type in ['党委系统', '政府办公室', '纪委监委', '发改委', '组织部', '宣传部']:
        prosp_base = 8.5
        prosp_base_label = f'核心部门({sys_type})'
    elif sys_type in ['公安系统', '法院系统', '检察院系统', '财政局']:
        prosp_base = 7.5
        prosp_base_label = f'政法财系统({sys_type})'
    elif '乡镇' in sys_type:
        prosp_base = 4.0
        prosp_base_label = f'基层岗位({sys_type})'
    else:
        prosp_base = 6.0
        prosp_base_label = sys_type or '普通部门'

    prospect_factors = []
    prospect_factors.append({
        'name': '部门权重',
        'value': prosp_base_label,
        'impact': f'{prosp_base:.1f}'
    })

    if district == '省直':
        prospect_factors.append({'name': '层级加成', 'value': '省直机关', 'impact': '+1.2'})
    elif district == '市直':
        prospect_factors.append({'name': '层级加成', 'value': '市直机关', 'impact': '+0.8'})
    else:
        prospect_factors.append({'name': '层级加成', 'value': district or '县级', 'impact': '-0.5'})

    if city == '郑州':
        prospect_factors.append({'name': '城市加成', 'value': '省会城市', 'impact': '+0.5'})
    elif city == '洛阳':
        prospect_factors.append({'name': '城市加成', 'value': '副中心城市', 'impact': '+0.3'})
    else:
        prospect_factors.append({'name': '城市加成', 'value': city, 'impact': '+0.0'})

    prospect_factors.append({'name': '最终得分', 'value': f'{prospect}', 'impact': ''})

    # ========================================
    # 难度标签和描述
    # ========================================
    if difficulty >= 8:
        diff_label = '🟢 容易'
        diff_desc = '上岸难度较低，进面分数线相对友好，性价比较高。'
    elif difficulty >= 6:
        diff_label = '🟡 中等'
        diff_desc = '难度适中，有一定竞争压力，认真备考有望上岸。'
    else:
        diff_label = '🔴 困难'
        diff_desc = '竞争较激烈，进面分数线较高，建议充分备考。'

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
    if sys_type in ['党委系统', '政府办公室', '纪委监委', '发改委']:
        prospect_detail += "核心部门，接触面广，晋升通道畅通。"
    elif '乡镇' in sys_type:
        prospect_detail += "基层岗位，锻炼机会多，晋升需较长时间积累。"
    else:
        prospect_detail += "常规晋升路径，工作稳定性高。"

    return {
        'difficulty_score': difficulty,
        'difficulty_label': diff_label,
        'difficulty_detail': difficulty_detail,
        'difficulty_factors': diff_factors,
        'difficulty_rule': difficulty_rule,
        'region_score': region,
        'region_detail': region_detail,
        'region_factors': region_factors,
        'region_rule': region_rule,
        'salary_score': salary,
        'salary_detail': salary_detail,
        'salary_factors': salary_factors,
        'salary_rule': salary_rule,
        'prospect_score': prospect,
        'prospect_detail': prospect_detail,
        'prospect_factors': prospect_factors,
        'prospect_rule': prospect_rule,
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
