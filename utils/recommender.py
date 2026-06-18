#!/usr/bin/env python3
"""
岗位推荐逻辑
基于用户画像匹配最合适的岗位
"""
from .query import search_positions, get_db


def recommend_for_user(major, education, city, political=None, experience=None, top_n=10):
    """基于用户条件推荐岗位"""
    conn = get_db()

    # 先精确匹配
    exact = search_positions(
        major=major, education=education, city=city,
        political=political, experience=experience,
        per_page=top_n, sort_by='avg_score', order='ASC'
    )

    results = exact['rows'][:top_n]

    # 如果精确匹配不够，放宽条件
    if len(results) < top_n:
        fuzzy = search_positions(
            major=major, education=education,
            political=political, experience=experience,
            per_page=top_n - len(results), sort_by='avg_score', order='ASC'
        )
        seen = {r['id'] for r in results}
        for item in fuzzy['rows']:
            if item['id'] not in seen:
                results.append(item)
                seen.add(item['id'])
                if len(results) >= top_n:
                    break

    # 为每个推荐添加评分
    from .scoring import get_score_detail
    for r in results:
        r['scoring'] = get_score_detail(r)

    conn.close()
    return results


def similar_positions(position_id, limit=5):
    """找到相似岗位"""
    conn = get_db()
    pos = conn.execute("SELECT * FROM positions WHERE id = ?", (position_id,)).fetchone()
    if not pos:
        conn.close()
        return []

    city = pos['city']
    sys_type = pos['system_type']
    major = pos['major_requirement']
    year = pos['year']

    similar = search_positions(
        major=major.split('、')[0] if '、' in major else major,
        city=city,
        system_type=sys_type,
        year=year,
        per_page=limit + 1,
        sort_by='avg_score',
        order='ASC'
    )

    results = [i for i in similar['rows'] if i['id'] != position_id][:limit]
    conn.close()
    return results
