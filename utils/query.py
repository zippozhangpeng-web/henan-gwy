#!/usr/bin/env python3
"""
数据库查询逻辑模块
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'gwy_data.db')


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def search_positions(major=None, education=None, city=None, cities=None,
                     political=None, experience=None, year=None,
                     system_type=None, sort_by=None, order='ASC',
                     page=1, per_page=20):
    """综合搜索岗位"""
    conn = get_db()
    conditions = []
    params = []

    if year:
        conditions.append("year = ?")
        params.append(year)

    if major:
        conditions.append("major_requirement LIKE ?")
        params.append(f"%{major}%")

    if education:
        conditions.append("education LIKE ?")
        params.append(f"%{education}%")

    if city:
        conditions.append("city = ?")
        params.append(city)

    if cities and isinstance(cities, list) and len(cities) > 0:
        placeholders = ','.join(['?'] * len(cities))
        conditions.append(f"city IN ({placeholders})")
        params.extend(cities)

    if political:
        conditions.append("political_status = ?")
        params.append(political)

    if experience:
        conditions.append("experience_requirement = ?")
        params.append(experience)

    if system_type:
        conditions.append("system_type = ?")
        params.append(system_type)

    where = "WHERE " + " AND ".join(conditions) if conditions else ""
    
    # 排序
    order_by = "year DESC, id"
    if sort_by:
        valid_sort = ['year','recruit_num','min_score','avg_score','overall_score','city']
        if sort_by in valid_sort:
            if sort_by == 'overall_score':
                order_by = f"ps.overall_score {order}"
            else:
                order_by = f"p.{sort_by} {order}"

    # 总数
    count_sql = f"SELECT COUNT(*) FROM positions {where}"
    total = conn.execute(count_sql, params).fetchone()[0]

    # 分页
    offset = (page - 1) * per_page
    # 始终包含评分数据
    sql = f"SELECT p.*, ps.overall_score, ps.difficulty_score, ps.region_score, ps.salary_score, ps.prospect_score FROM positions p LEFT JOIN position_scores ps ON p.id = ps.position_id {where} ORDER BY {order_by} LIMIT ? OFFSET ?"
    rows = conn.execute(sql, params + [per_page, offset]).fetchall()
    conn.close()

    return {
        'total': total,
        'page': page,
        'per_page': per_page,
        'total_pages': (total + per_page - 1) // per_page,
        'rows': [dict(r) for r in rows]
    }


def get_position_detail(position_id):
    """获取岗位详情+评分"""
    conn = get_db()
    pos = conn.execute("SELECT * FROM positions WHERE id = ?", (position_id,)).fetchone()
    if not pos:
        conn.close()
        return None
    
    scores = conn.execute(
        "SELECT * FROM position_scores WHERE position_id = ?", (position_id,)
    ).fetchone()

    conn.close()
    return {
        'position': dict(pos),
        'scores': dict(scores) if scores else None
    }


def get_stats():
    """首页统计数据"""
    conn = get_db()
    stats = {}

    # 总岗位数
    stats['total_positions'] = conn.execute("SELECT COUNT(*) FROM positions").fetchone()[0]
    stats['total_recruit'] = conn.execute("SELECT SUM(recruit_num) FROM positions").fetchone()[0]

    # 按年份
    by_year = conn.execute(
        "SELECT year, COUNT(*) as cnt, SUM(recruit_num) as total_recruit FROM positions GROUP BY year ORDER BY year"
    ).fetchall()
    stats['by_year'] = [dict(r) for r in by_year]

    # 按地市
    by_city = conn.execute(
        "SELECT city, COUNT(*) as cnt, SUM(recruit_num) as total_recruit FROM positions GROUP BY city ORDER BY cnt DESC"
    ).fetchall()
    stats['by_city'] = [dict(r) for r in by_city]

    # 按系统
    by_system = conn.execute(
        "SELECT system_type, COUNT(*) as cnt FROM positions GROUP BY system_type ORDER BY cnt DESC"
    ).fetchall()
    stats['by_system'] = [dict(r) for r in by_system]

    # 按学历
    by_edu = conn.execute(
        "SELECT education, COUNT(*) as cnt FROM positions GROUP BY education ORDER BY cnt DESC"
    ).fetchall()
    stats['by_edu'] = [dict(r) for r in by_edu]

    # 平均分数线（可能为空）
    avg_score = conn.execute("SELECT AVG(avg_score) FROM positions WHERE avg_score > 0").fetchone()[0]
    stats['avg_score'] = round(float(avg_score), 2) if avg_score else 0

    # 热门/推荐岗位（avg_score为空时按招录人数排序）
    hardest = conn.execute(
        "SELECT id, unit, position_name, city, recruit_num FROM positions ORDER BY recruit_num DESC LIMIT 5"
    ).fetchall()
    stats['hardest'] = [dict(r) for r in hardest]

    easiest = conn.execute(
        "SELECT id, unit, position_name, city, recruit_num FROM positions WHERE recruit_num > 0 ORDER BY recruit_num ASC LIMIT 5"
    ).fetchall()
    stats['easiest'] = [dict(r) for r in easiest]

    conn.close()
    return stats


def get_cities():
    """获取所有城市列表"""
    conn = get_db()
    cities = conn.execute(
        "SELECT city, COUNT(*) as cnt FROM positions GROUP BY city ORDER BY cnt DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in cities]


def search_history(major=None, education=None, city=None, political=None, experience=None, limit=10):
    """获取搜索历史/相似搜索"""
    conn = get_db()
    conditions = []
    params = []
    if major:
        conditions.append("major = ?")
        params.append(major)
    if education:
        conditions.append("education = ?")
        params.append(education)
    if city:
        conditions.append("city = ?")
        params.append(city)
    
    where = "WHERE " + " AND ".join(conditions) if conditions else ""
    rows = conn.execute(f"SELECT * FROM search_history {where} ORDER BY created_at DESC LIMIT ?", params + [limit]).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_years():
    """获取数据库中所有年份"""
    conn = get_db()
    years = conn.execute("SELECT DISTINCT year FROM positions ORDER BY year DESC").fetchall()
    conn.close()
    return [r[0] for r in years]


def get_system_types():
    """获取所有系统类别"""
    conn = get_db()
    types = conn.execute("SELECT DISTINCT system_type FROM positions ORDER BY system_type").fetchall()
    conn.close()
    return [r[0] for r in types]
