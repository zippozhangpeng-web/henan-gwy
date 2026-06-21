#!/usr/bin/env python3
"""
历史分数波动率分析模块
查询同单位+同岗位名跨年分数，计算波动指标
"""
import sqlite3
import os
import math

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'gwy_data.db')


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_historical_scores(position):
    """
    查询同单位+同名岗位的历年分数
    输入：当前position dict（包含 unit, position_name）
    输出：[{year, min_score, max_score, avg_score, is_estimated}...] 按年份升序
    """
    conn = get_db()
    rows = conn.execute(
        """SELECT year,
                  MIN(min_score) as min_score,
                  MAX(max_score) as max_score,
                  AVG(avg_score) as avg_score,
                  MAX(is_estimated) as is_estimated
           FROM positions
           WHERE unit = ? AND position_name = ?
             AND min_score IS NOT NULL AND min_score > 0
           GROUP BY year
           ORDER BY year ASC""",
        (position['unit'], position['position_name'])
    ).fetchall()
    conn.close()

    result = []
    for r in rows:
        result.append({
            'year': r['year'],
            'min_score': round(r['min_score'], 2) if r['min_score'] else None,
            'max_score': round(r['max_score'], 2) if r['max_score'] else None,
            'avg_score': round(r['avg_score'], 2) if r['avg_score'] else None,
            'is_estimated': bool(r['is_estimated']) if r['is_estimated'] is not None else False
        })
    return result


def _linear_regression_slope(xs, ys):
    """简易线性回归斜率"""
    n = len(xs)
    if n < 2:
        return 0.0
    mean_x = sum(xs) / n
    mean_y = sum(ys) / n
    num = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    den = sum((x - mean_x) ** 2 for x in xs)
    if abs(den) < 1e-9:
        return 0.0
    return num / den


def calculate_volatility(scores_list):
    """
    计算波动指标
    输入：分数列表 [{year, min_score, max_score, avg_score, is_estimated}...]
    输出：{range, std_dev, cv, trend_type, trend_slope, highest, lowest, year_count}
    """
    if not scores_list:
        return {
            'range': 0, 'std_dev': 0, 'cv': 0,
            'trend_type': '数据不足', 'trend_slope': 0,
            'highest': None, 'lowest': None, 'year_count': 0
        }

    # 使用 avg_score 作为主要分析指标，回退到 min_score
    values = [s['avg_score'] if s['avg_score'] else s['min_score'] for s in scores_list]
    years = [s['year'] for s in scores_list]
    n = len(values)

    # 最高/最低
    highest_idx = max(range(n), key=lambda i: values[i])
    lowest_idx = min(range(n), key=lambda i: values[i])

    highest = {
        'year': scores_list[highest_idx]['year'],
        'value': values[highest_idx],
        'is_estimated': scores_list[highest_idx]['is_estimated']
    }
    lowest = {
        'year': scores_list[lowest_idx]['year'],
        'value': values[lowest_idx],
        'is_estimated': scores_list[lowest_idx]['is_estimated']
    }

    score_range = round(highest['value'] - lowest['value'], 2)

    # 标准差
    mean_val = sum(values) / n
    variance = sum((v - mean_val) ** 2 for v in values) / n
    std_dev = round(math.sqrt(variance), 2)

    # 变异系数 CV = sigma / mu
    cv = round(std_dev / mean_val, 2) if mean_val > 0 else 0

    # 趋势判断：线性回归斜率 + 年际方向变化
    slope = _linear_regression_slope(years, values)
    # Normalize slope by mean to get relative slope
    rel_slope = slope / mean_val if mean_val > 0 else 0

    # Count reversals (相邻两年方向变化次数)
    reversals = 0
    if n >= 3:
        for i in range(1, n - 1):
            prev_diff = values[i] - values[i - 1]
            next_diff = values[i + 1] - values[i]
            if prev_diff * next_diff < 0:  # direction changed
                reversals += 1

    if n < 2:
        trend_type = '数据不足'
    elif n == 2:
        if abs(rel_slope) < 0.02:
            trend_type = '稳定'
        elif slope > 0:
            trend_type = '上升'
        else:
            trend_type = '下降'
    else:
        if abs(rel_slope) < 0.015:
            trend_type = '稳定'
        elif reversals >= n - 2:
            # Every year flipped direction → 震荡
            trend_type = '震荡'
        elif reversals >= 1 and abs(rel_slope) < 0.04:
            trend_type = '震荡'
        elif slope > 0:
            trend_type = '上升'
        elif slope < 0:
            trend_type = '下降'
        else:
            trend_type = '稳定'

    return {
        'range': score_range,
        'std_dev': std_dev,
        'cv': cv,
        'trend_type': trend_type,
        'trend_slope': round(rel_slope, 4),
        'highest': highest,
        'lowest': lowest,
        'year_count': n
    }


def get_position_volatility(position_id):
    """
    获取岗位完整波动分析数据
    输入：position_id
    输出：{scores, volatility, summary_text, has_enough_data}
    """
    conn = get_db()
    pos = conn.execute("SELECT * FROM positions WHERE id = ?", (position_id,)).fetchone()
    if not pos:
        conn.close()
        return {'has_enough_data': False, 'scores': [], 'volatility': {}, 'summary_text': ''}

    position = dict(pos)
    conn.close()

    scores = get_historical_scores(position)
    volatility = calculate_volatility(scores)

    # 生成摘要文字
    summary_text = _generate_summary(volatility, scores)

    return {
        'scores': scores,
        'volatility': volatility,
        'summary_text': summary_text,
        'has_enough_data': len(scores) >= 2
    }


def _generate_summary(volatility, scores):
    """根据波动数据生成人类可读的摘要"""
    if not scores or len(scores) < 2:
        return '仅1年数据，不足以分析趋势'

    highest = volatility.get('highest', {})
    lowest = volatility.get('lowest', {})

    parts = []
    parts.append(f"该岗位近{volatility['year_count']}年进面分波动范围{lowest['value']}–{highest['value']}分")

    trend = volatility['trend_type']
    if trend == '上升':
        parts.append('呈上升趋势，竞争逐年加剧，建议尽早报考')
    elif trend == '下降':
        parts.append('呈下降趋势，报考性价比相对提升')
    elif trend == '震荡':
        parts.append('呈震荡态势，分数波动较大，大小年特征明显')
    elif trend == '稳定':
        parts.append('分数相对稳定，波动在正常范围')

    return '；'.join(parts)
