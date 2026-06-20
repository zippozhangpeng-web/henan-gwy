#!/usr/bin/env python3
"""
河南省考岗位数据爬虫 & 数据导入
工作原理：从 henan.gov.cn 的官方公告中获取职位表 Excel 附件并解析入库
"""
import os, sys, sqlite3, requests

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))

# 每年的公告页 URL 及对应职位表附件链接（2021+）
# 官方数据源：henan.gov.cn → 公务员招录专栏
ANNUAL_DATA = [
    {
        'year': 2026,
        'announcement': 'https://www.henan.gov.cn/2026/01-05/3281668.html',
        'file_url': 'https://xcoss.henan.gov.cn/typtfile/20260105/37274f6c016a48b4bcdc66e7f11464cf.xlsx',
        'type': 'xlsx',
        'recruit_count': 10429,
    },
    {
        'year': 2025,
        'announcement': 'https://www.henan.gov.cn/2025/01-08/3109670.html',
        'file_url': 'https://oss.henan.gov.cn/typtfile/20250108/a72f250122da4d7e99e445cb55483074.xls',
        'type': 'xls',
        'recruit_count': 10993,
    },
    {
        'year': 2024,
        'announcement': 'https://www.henan.gov.cn/2024/01-16/2886224.html',
        'file_url': 'https://oss.henan.gov.cn/typtfile/20240116/046f9d69c3b84434a5dce577491f3447.xls',
        'type': 'xls',
        'recruit_count': 9900,
    },
    {
        'year': 2023,
        'announcement': 'https://hrss.henan.gov.cn/2023/01-05/2667230.html',
        'file_url': 'https://oss.henan.gov.cn/typtfile/20230105/0b92bcc83e7344188f9706079320a4b5.xls',
        'type': 'xls',
        'recruit_count': 9134,
    },
    {
        'year': 2022,
        'announcement': 'https://hrss.henan.gov.cn/2022/02-11/2396904.html',
        'file_url': 'https://oss.henan.gov.cn/typtfile/20220211/08bdae4b08694ba296359a47db47fefb.xls',
        'type': 'xls',
        'recruit_count': 7993,
    },
]


def run_import():
    """运行 import 脚本"""
    print('=' * 60)
    print('🏛️  河南省考岗位数据导入工具')
    print('=' * 60)
    os.chdir(PROJECT_DIR)
    rc = os.system(f'{sys.executable} download_real_data.py')
    if rc != 0:
        print('❌ 导入失败')
        return False
    return True


def check_stats():
    """检查数据库统计"""
    db_path = os.path.join(PROJECT_DIR, 'gwy_data.db')
    if not os.path.exists(db_path):
        print('❌ 数据库不存在')
        return

    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM positions')
    total = c.fetchone()[0]
    c.execute('SELECT year, COUNT(*), SUM(recruit_num) FROM positions GROUP BY year ORDER BY year')
    print(f'\n📊 数据库统计 (共 {total} 条记录)')
    print(f'{"="*40}')
    for y, cnt, rn in c.fetchall():
        expected = next((d['recruit_count'] for d in ANNUAL_DATA if d['year'] == y), 0)
        match = '✅' if int(rn) == expected else '⚠️'
        print(f'  {y}年: {cnt} 岗位 / {int(rn)} 人 (官方: {expected}) {match}')
    conn.close()


if __name__ == '__main__':
    import urllib3
    urllib3.disable_warnings()

    if len(sys.argv) > 1 and sys.argv[1] == '--stats':
        check_stats()
    else:
        run_import()
