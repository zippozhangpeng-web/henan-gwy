#!/usr/bin/env python3
"""
河南公考岗位情报站 - Flask 主入口
"""
import os
import sys
from flask import Flask, render_template, request, jsonify

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.query import (
    search_positions, get_position_detail, get_stats,
    get_cities, get_years, get_system_types
)
from utils.scoring import get_score_detail

import json

app = Flask(__name__)
app.config['SECRET_KEY'] = 'henan-gwy-secret-2026'


@app.route('/health')
def health():
    return {"status": "ok", "name": "好风公考情报站"}


@app.route('/')
def index():
    """首页"""
    try:
        stats = get_stats()
        years = get_years()
        cities = get_cities()
        return render_template('index.html', stats=stats, years=years, cities=cities)
    except Exception as e:
        print(f"首页渲染异常: {e}")
        import traceback; traceback.print_exc()
        stats = {'total_positions': 0, 'total_recruit': 0, 'by_year': [], 'by_city': [],
                 'by_system': [], 'by_edu': [], 'avg_score': 0, 'hardest': [], 'easiest': []}
        return render_template('index.html', stats=stats, years=[], cities=[])


@app.route('/search')
def search():
    """岗位搜索"""
    major = request.args.get('major', '').strip()
    education = request.args.get('education', '').strip()
    city = request.args.get('city', '').strip()
    cities_param = request.args.get('cities', '').strip()
    political = request.args.get('political', '').strip()
    experience = request.args.get('experience', '').strip()
    year = request.args.get('year', '').strip()
    sort_by = request.args.get('sort_by', '').strip()
    order = request.args.get('order', 'ASC').strip()
    page = request.args.get('page', 1, type=int)

    # 处理多城市
    cities_list = None
    if cities_param:
        cities_list = [c.strip() for c in cities_param.split(',') if c.strip()]

    result = search_positions(
        major=major if major else None,
        education=education if education else None,
        city=city if city else None,
        cities=cities_list,
        political=political if political else None,
        experience=experience if experience else None,
        year=int(year) if year else None,
        sort_by=sort_by if sort_by else None,
        order=order,
        page=page,
        per_page=20
    )

    years = get_years()
    cities = get_cities()

    # 构建查询参数（用于分页）
    query_params = '&'.join(
        f'{k}={v}' for k, v in request.args.items()
        if k != 'page' and v
    )

    return render_template(
        'search.html',
        result=result,
        years=years,
        cities=cities,
        sort_by=request.args.get('sort_by', ''),
        order=request.args.get('order', ''),
        query_params=query_params
    )


@app.route('/position/<int:position_id>')
def position_detail(position_id):
    """岗位情报详情页"""
    detail = get_position_detail(position_id)
    if not detail:
        return render_template('base.html', content='岗位不存在'), 404

    pos = detail['position']
    # 动态计算评分
    if detail['scores']:
        scores = {
            'difficulty_score': detail['scores']['difficulty_score'],
            'difficulty_label': get_difficulty_label(detail['scores']['difficulty_score']),
            'difficulty_detail': detail['scores']['difficulty_detail'],
            'region_score': detail['scores']['region_score'],
            'region_detail': detail['scores']['region_detail'],
            'salary_score': detail['scores']['salary_score'],
            'salary_detail': detail['scores']['salary_detail'],
            'prospect_score': detail['scores']['prospect_score'],
            'prospect_detail': detail['scores']['prospect_detail'],
            'overall_score': detail['scores']['overall_score'],
            'city_data': get_score_detail(pos)['city_data']
        }
    else:
        scores = get_score_detail(pos)

    return render_template('position.html', pos=pos, scores=scores, scores_json=json.dumps(scores, ensure_ascii=False))


def get_difficulty_label(score):
    if score >= 7:
        return '🔴 困难'
    elif score >= 5:
        return '🟡 中等'
    return '🟢 容易'


@app.route('/analysis')
def analysis():
    """数据分析页"""
    stats = get_stats()

    # 为各城市计算平均分数线
    import sqlite3
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'gwy_data.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    city_scores = conn.execute(
        "SELECT city, AVG(avg_score) as avg_score, COUNT(*) as cnt, SUM(recruit_num) as total_recruit FROM positions WHERE avg_score > 0 GROUP BY city ORDER BY cnt DESC"
    ).fetchall()
    conn.close()

    stats['by_city'] = [dict(r) for r in city_scores]
    return render_template('analysis.html', stats=stats)


@app.route('/about')
def about():
    """关于页面"""
    return render_template('about.html')


@app.errorhandler(404)
def not_found(e):
    return render_template('base.html', content='页面不存在'), 404


@app.errorhandler(500)
def server_error(e):
    return render_template('base.html', content='服务器错误'), 500


if __name__ == '__main__':
    # 确保数据库存在
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'gwy_data.db')
    if not os.path.exists(db_path):
        print("⚠️  数据库不存在，正在从官方数据导入...")
        import subprocess
        subprocess.run([sys.executable, 'download_real_data.py'], cwd=os.path.dirname(os.path.abspath(__file__)))

    print("=" * 60)
    print("🏛️  河南公考岗位情报站")
    print("=" * 60)
    print(f"📡 访问地址: http://127.0.0.1:5000")
    print(f"📡 局域网地址: http://0.0.0.0:5000")
    print("=" * 60)
    debug = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
    port = int(os.getenv('PORT', '5050'))
    app.run(host='0.0.0.0', port=port, debug=debug)
