#!/usr/bin/env python3
"""
河南公考岗位数据爬虫
从 hnrsks.com 抓取公告页，提取职位表附件链接，下载并解析 Excel 文件

使用说明：
1. 确保已安装依赖: pip install requests beautifulsoup4 openpyxl lxml
2. 确保代理可用: export HTTP_PROXY=http://127.0.0.1:1082 HTTPS_PROXY=http://127.0.0.1:1082
3. 运行: python scraper.py

注意：
- 如果官方下载失败，会给出提示手动下载路径
- 爬取的数据会存入 gwy_data.db
"""
import os
import sys
import re
import time
import sqlite3
import requests
from bs4 import BeautifulSoup
import openpyxl

# ===== 配置 =====
PROXY = os.environ.get('HTTP_PROXY', 'http://127.0.0.1:1082')
BASE_URL = "http://www.hnrsks.com"
LIST_URL = f"{BASE_URL}/sitesources/hnsrskszx/page_pc/gwyzt/index.html"
DOWNLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'downloads')
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'gwy_data.db')

# 历年公告页
YEAR_URLS = {
    2026: f"{BASE_URL}/sitesources/hnsrskszx/page_pc/hnstykslygwyzl/dnzkgg/article197f077a15884b4dbfa18ee21e68319f.html",
    2024: f"{BASE_URL}/sitesources/hnsrskszx/page_pc/gwyzt/zkgg/articlea535d08f8be14e2ea47dc11681d4d441.html",
    2023: f"{BASE_URL}/sitesources/hnsrskszx/page_pc/zngg/article93e63dd552e8467facc8689e3f77aa0c.html",
}

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9',
    'Accept-Encoding': 'gzip, deflate',
    'Connection': 'keep-alive',
}

os.makedirs(DOWNLOAD_DIR, exist_ok=True)


def get_session():
    """创建带代理的 session"""
    session = requests.Session()
    session.headers.update(HEADERS)
    session.proxies = {
        'http': PROXY,
        'https': PROXY,
    }
    return session


def fetch_page(url, session):
    """抓取页面"""
    try:
        print(f"  📡 请求: {url}")
        resp = session.get(url, timeout=30, verify=False)
        resp.encoding = resp.apparent_encoding or 'utf-8'
        return resp.text
    except requests.RequestException as e:
        print(f"  ❌ 请求失败: {e}")
        print(f"  💡 提示: 请确保代理 {PROXY} 可用，或在系统设置中配置代理")
        return None


def find_excel_links(html, base_url):
    """从 HTML 中提取 Excel 附件链接"""
    soup = BeautifulSoup(html, 'lxml')
    links = []

    # 查找所有链接
    for a in soup.find_all('a', href=True):
        href = a['href']
        text = a.get_text(strip=True)

        # 匹配 .xls 或 .xlsx 文件
        if re.search(r'\.xlsx?$', href, re.IGNORECASE):
            full_url = href if href.startswith('http') else f"{base_url}{href}"
            links.append({
                'url': full_url,
                'text': text,
                'filename': href.split('/')[-1]
            })

    # 也查找包含"职位表"、"岗位表"、"附件"等关键词的链接
    for a in soup.find_all('a', href=True):
        text = a.get_text(strip=True)
        href = a['href']
        if any(kw in text for kw in ['职位表', '岗位表', '招录职位', '附件', '职位信息']):
            full_url = href if href.startswith('http') else f"{base_url}{href}"
            if full_url not in [l['url'] for l in links]:
                links.append({
                    'url': full_url,
                    'text': text,
                    'filename': href.split('/')[-1]
                })

    return links


def download_file(url, filename, session):
    """下载文件"""
    filepath = os.path.join(DOWNLOAD_DIR, filename)
    print(f"  📥 下载: {filename}")
    try:
        resp = session.get(url, timeout=60, stream=True, verify=False)
        if resp.status_code == 200:
            with open(filepath, 'wb') as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"  ✅ 已保存: {filepath}")
            return filepath
        else:
            print(f"  ❌ 下载失败 HTTP {resp.status_code}")
            return None
    except Exception as e:
        print(f"  ❌ 下载异常: {e}")
        return None


def parse_excel(filepath, year):
    """解析职位表 Excel"""
    print(f"  📊 解析: {filepath}")
    wb = openpyxl.load_workbook(filepath, read_only=True, data_only=True)
    ws = wb.active

    positions = []
    headers = []
    header_row = None

    for row_idx, row in enumerate(ws.iter_rows(values_only=True), 1):
        cells = [str(c).strip() if c is not None else '' for c in row]

        # 查找表头行（包含"招录机关"、"职位名称"等关键词）
        if row_idx <= 5:
            if any(kw in ''.join(cells) for kw in ['招录机关', '职位名称', '职位代码']):
                headers = cells
                header_row = row_idx
                print(f"  📋 找到表头 (第{row_idx}行): {headers[:5]}...")
                continue

        if header_row and row_idx > header_row:
            # 跳过空行
            if not any(cells):
                continue
            # 跳过合并说明行
            if len(''.join(cells)) < 5:
                continue

            positions.append({
                'row_data': cells,
                'headers': headers,
                'year': year
            })

    print(f"  ✅ 解析完成: {len(positions)} 条岗位数据")
    return positions, headers


def save_to_db(positions, headers, year):
    """保存到数据库"""
    if not positions:
        print("  ⚠️  无数据可保存")
        return

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # 确保表存在
    c.execute('''CREATE TABLE IF NOT EXISTS positions_scraped (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        year INTEGER, unit TEXT, position_name TEXT, position_code TEXT,
        recruit_num INTEGER, major_requirement TEXT, education TEXT,
        degree TEXT, political_status TEXT, experience_requirement TEXT,
        other_conditions TEXT, notes TEXT, exam_category TEXT,
        interview_ratio TEXT, raw_data TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    count = 0
    for pos in positions:
        row = pos['row_data']
        try:
            c.execute('''INSERT INTO positions_scraped
                (year, unit, position_name, raw_data)
                VALUES (?, ?, ?, ?)''',
                (year, row[0] if len(row) > 0 else '',
                 row[1] if len(row) > 1 else '',
                 '|'.join(row)))
            count += 1
        except Exception as e:
            print(f"  ⚠️  插入失败: {e}")

    conn.commit()
    conn.close()
    print(f"  ✅ 已保存 {count} 条到数据库")


def scrape_year(year, url, session):
    """爬取指定年份"""
    print(f"\n{'='*50}")
    print(f"📅 爬取 {year} 年数据")
    print(f"{'='*50}")

    html = fetch_page(url, session)
    if not html:
        print(f"  ⚠️  {year}年页面获取失败，请手动下载职位表")
        print(f"  📎 公告地址: {url}")
        print(f"  📁 手动下载后放入: {DOWNLOAD_DIR}")
        return

    links = find_excel_links(html, BASE_URL)
    if not links:
        print(f"  ⚠️  未找到 Excel 附件链接")
        print(f"  📎 请手动访问公告页面下载: {url}")
        return

    print(f"  📎 找到 {len(links)} 个附件链接:")
    for l in links:
        print(f"     - {l['text'][:50]}: {l['url'][:80]}")

    for link in links:
        filepath = download_file(link['url'], f"{year}_{link['filename']}", session)
        if filepath:
            positions, headers = parse_excel(filepath, year)
            save_to_db(positions, headers, year)


def main():
    """主函数"""
    print("=" * 60)
    print("🏛️  河南公考岗位数据爬虫")
    print(f"🔌 代理: {PROXY}")
    print("=" * 60)

    # 禁用 SSL 警告
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    session = get_session()

    for year, url in YEAR_URLS.items():
        scrape_year(year, url, session)
        time.sleep(2)  # 礼貌间隔

    print(f"\n{'='*60}")
    print("✅ 爬取完成")
    print(f"📁 下载文件目录: {DOWNLOAD_DIR}")
    print(f"🗄️  数据库: {DB_PATH}")
    print("=" * 60)


if __name__ == '__main__':
    main()
