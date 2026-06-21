#!/usr/bin/env python3
"""
河南公考岗位情报站 - Flask 主入口
"""
import os
import sys
import sqlite3
from flask import Flask, render_template, request, jsonify

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.query import (
    search_positions, get_position_detail, get_stats,
    get_cities, get_years, get_system_types
)
from utils.scoring import get_score_detail
from utils.volatility import get_position_volatility

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
                 'by_system': [], 'by_edu': [], 'avg_score': 0, 'hardest': [], 'easiest': [],
                 'top_positions': []}
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
    # 默认选中2025年，选"全部"时传 year=all
    current_year = year if year else '2025'
    if not year:
        year = '2025'
    elif year == 'all':
        year = ''
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
        current_year=current_year,
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
        s = detail['scores']
        scores = {
            'difficulty_score': s['difficulty_score'] or 5.0,
            'difficulty_label': get_difficulty_label(s['difficulty_score'] or 5.0),
            'difficulty_detail': s['difficulty_detail'] or '',
            'difficulty_factors': s.get('difficulty_factors') or [],
            'difficulty_rule': s.get('difficulty_rule', ''),
            'region_score': s['region_score'] or 5.0,
            'region_detail': s['region_detail'] or '',
            'region_factors': s.get('region_factors') or [],
            'region_rule': s.get('region_rule', ''),
            'salary_score': s['salary_score'] or 5.0,
            'salary_detail': s['salary_detail'] or '',
            'salary_factors': s.get('salary_factors') or [],
            'salary_rule': s.get('salary_rule', ''),
            'prospect_score': s['prospect_score'] or 5.0,
            'prospect_detail': s['prospect_detail'] or '',
            'prospect_factors': s.get('prospect_factors') or [],
            'prospect_rule': s.get('prospect_rule', ''),
            'overall_score': s['overall_score'] or 5.0,
            'city_data': get_score_detail(pos)['city_data']
        }
        # 如果DB中factors为空，动态补充
        if not scores['difficulty_factors']:
            fresh = get_score_detail(pos)
            for dim in ['difficulty', 'region', 'salary', 'prospect']:
                scores[f'{dim}_factors'] = fresh.get(f'{dim}_factors', [])
                scores[f'{dim}_rule'] = fresh.get(f'{dim}_rule', '')
    else:
        scores = get_score_detail(pos)

    # 波动率分析
    volatility = get_position_volatility(position_id)

    # 将波动趋势融入难度分析
    if volatility['has_enough_data'] and scores.get('difficulty_detail'):
        v = volatility['volatility']
        extra = f'该岗位近{len(volatility["scores"])}年进面分波动范围{v["lowest"]["value"]}-{v["highest"]["value"]}分'
        if v['trend_type'] == '上升':
            extra += '，呈上升趋势，竞争逐年加大。'
        elif v['trend_type'] == '下降':
            extra += '，呈下降趋势。'
        elif v['trend_type'] == '震荡':
            extra += '，呈震荡态势。'
        else:
            extra += '，分数稳定。'
        scores['difficulty_detail'] = scores['difficulty_detail'] + ' ' + extra

    return render_template('position_detail.html', pos=pos, scores=scores, volatility=volatility,
                           scores_json=json.dumps(scores, ensure_ascii=False))


def get_difficulty_label(score):
    if score >= 7:
        return '🟢 容易'
    elif score >= 5:
        return '🟡 中等'
    return '🔴 困难'


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


@app.route('/api/position/<int:position_id>/scores')
def api_position_scores(position_id):
    """API: 获取岗位评分详情（含因子明细）"""
    detail = get_position_detail(position_id)
    if not detail:
        return jsonify({'error': '岗位不存在'}), 404
    
    pos = detail['position']
    if detail['scores']:
        s = detail['scores']
        # 如果DB中没有factors，动态生成
        if not s.get('difficulty_factors'):
            fresh = get_score_detail(pos)
        else:
            fresh = None
        
        scores = {
            'difficulty_score': s['difficulty_score'] or 5.0,
            'difficulty_label': get_difficulty_label(s['difficulty_score'] or 5.0),
            'difficulty_factors': s.get('difficulty_factors') or (fresh['difficulty_factors'] if fresh else []),
            'difficulty_rule': s.get('difficulty_rule') or (fresh['difficulty_rule'] if fresh else ''),
            'region_score': s['region_score'] or 5.0,
            'region_factors': s.get('region_factors') or (fresh['region_factors'] if fresh else []),
            'region_rule': s.get('region_rule') or (fresh['region_rule'] if fresh else ''),
            'salary_score': s['salary_score'] or 5.0,
            'salary_factors': s.get('salary_factors') or (fresh['salary_factors'] if fresh else []),
            'salary_rule': s.get('salary_rule') or (fresh['salary_rule'] if fresh else ''),
            'prospect_score': s['prospect_score'] or 5.0,
            'prospect_factors': s.get('prospect_factors') or (fresh['prospect_factors'] if fresh else []),
            'prospect_rule': s.get('prospect_rule') or (fresh['prospect_rule'] if fresh else ''),
            'overall_score': s['overall_score'] or 5.0,
        }
    else:
        scores = get_score_detail(pos)
    return jsonify(scores)


@app.errorhandler(404)
def not_found(e):
    return render_template('base.html', content='页面不存在'), 404


@app.errorhandler(500)
def server_error(e):
    return render_template('base.html', content='服务器错误'), 500


if __name__ == '__main__':
    # 确保数据库存在
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'gwy_data.db')
    # 检查数据库状态
    need_rebuild = False
    need_scores = False
    if not os.path.exists(db_path):
        need_rebuild = True
    else:
        try:
            c = sqlite3.connect(db_path)
            cnt = c.execute('SELECT COUNT(*) FROM positions').fetchone()[0]
            score_cnt = c.execute('SELECT COUNT(*) FROM positions WHERE min_score IS NOT NULL').fetchone()[0]
            c.close()
            if cnt < 10000:
                need_rebuild = True
                print(f"⚠️  数据库仅有 {cnt} 条数据，重新导入...")
            elif score_cnt < 1000:
                need_scores = True
                print(f"⚠️  数据库有 {cnt} 条岗位但仅 {score_cnt} 条有进面分，导入分数...")
        except:
            need_rebuild = True

    import subprocess
    root_dir = os.path.dirname(os.path.abspath(__file__))

    if need_rebuild:
        print("⏳ 正在从官方数据重新构建数据库...")
        subprocess.run([sys.executable, 'download_real_data.py'], cwd=root_dir)
        need_scores = True

    if need_scores:
        print("⏳ 正在导入面试进面分数数据...")
        for script in ['import_scores.py', 'import_pdf_scores.py']:
            sp = os.path.join(root_dir, script)
            if os.path.exists(sp):
                subprocess.run([sys.executable, script], cwd=root_dir)

    print("=" * 60)
    print("🏛️  河南公考岗位情报站")
    print("=" * 60)
    print(f"📡 访问地址: http://127.0.0.1:5000")
    print(f"📡 局域网地址: http://0.0.0.0:5000")
    print("=" * 60)
    debug = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
    port = int(os.getenv('PORT', '5050'))
    app.run(host='0.0.0.0', port=port, debug=debug)
