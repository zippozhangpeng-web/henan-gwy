#!/usr/bin/env python3
"""
清理2025年异常进面分数数据
- min_score=0.0 的设为 NULL（无数据比假数据好）
- min_score>100 的整行三个分数都设为 NULL（疑似笔试总分）
- avg_score>100 的设为 NULL（保留有效 min_score）
- max_score>100 的设为 NULL（保留有效 min/avg）
"""
import sqlite3
import os
import sys

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'gwy_data.db')


def clean_scores(dry_run=False):
    """清理异常分数，dry_run=True 时只统计不执行"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    print("=" * 60)
    print("🧹 进面分数清理工具")
    print("=" * 60)

    # 清理前统计
    before_total = conn.execute("SELECT COUNT(*) FROM positions").fetchone()[0]
    before_with_score = conn.execute(
        "SELECT COUNT(*) FROM positions WHERE min_score IS NOT NULL AND min_score > 0 AND min_score <= 100"
    ).fetchone()[0]

    print(f"\n📊 清理前状态:")
    print(f"  总岗位数: {before_total}")
    print(f"  有效进面分岗位: {before_with_score}")

    anomalies = {
        'min_zero': conn.execute("SELECT COUNT(*) FROM positions WHERE min_score = 0.0").fetchone()[0],
        'min_high': conn.execute("SELECT COUNT(*) FROM positions WHERE min_score > 100").fetchone()[0],
        'avg_high': conn.execute("SELECT COUNT(*) FROM positions WHERE avg_score > 100").fetchone()[0],
        'max_high': conn.execute("SELECT COUNT(*) FROM positions WHERE max_score > 100").fetchone()[0],
    }

    print(f"\n🔍 检测到异常:")
    print(f"  min_score = 0.0: {anomalies['min_zero']} 条")
    print(f"  min_score > 100: {anomalies['min_high']} 条")
    print(f"  avg_score > 100: {anomalies['avg_high']} 条")
    print(f"  max_score > 100: {anomalies['max_high']} 条")

    if dry_run:
        print("\n⚠️  DRY RUN 模式：以上仅为统计，未执行任何修改。")
        print("   如需执行清理，请运行: python3 clean_scores.py --apply")
        conn.close()
        return

    print("\n🔧 正在清理...")

    # 1. min_score=0.0 → NULL（这些可能还有有效的 avg/max，一起清）
    result = conn.execute(
        "UPDATE positions SET min_score = NULL, avg_score = NULL, max_score = NULL WHERE min_score = 0.0"
    )
    print(f"  ✅ min_score=0.0: {result.rowcount} 条已设为 NULL（含 avg/max）")

    # 2. min_score>100 → 全部三个设为 NULL（疑似笔试总分）
    result = conn.execute(
        "UPDATE positions SET min_score = NULL, avg_score = NULL, max_score = NULL WHERE min_score > 100"
    )
    print(f"  ✅ min_score>100: {result.rowcount} 条已设为 NULL")

    # 3. avg_score>100 → 只清 avg 和 max（min 可能有效）
    result = conn.execute(
        "UPDATE positions SET avg_score = NULL WHERE avg_score > 100"
    )
    print(f"  ✅ avg_score>100: {result.rowcount} 条 avg_score 已设为 NULL")

    # 4. max_score>100 → 只清 max（min/avg 可能有效）
    result = conn.execute(
        "UPDATE positions SET max_score = NULL WHERE max_score > 100"
    )
    print(f"  ✅ max_score>100: {result.rowcount} 条 max_score 已设为 NULL")

    conn.commit()

    # 清理后统计
    after_with_score = conn.execute(
        "SELECT COUNT(*) FROM positions WHERE min_score IS NOT NULL AND min_score > 0 AND min_score <= 100"
    ).fetchone()[0]

    # 按年统计覆盖率
    print(f"\n📊 清理后状态:")
    print(f"  有效进面分岗位: {after_with_score}")

    print(f"\n📅 各年份覆盖率:")
    years = conn.execute(
        """SELECT year, 
                  COUNT(*) as total,
                  SUM(CASE WHEN min_score IS NOT NULL AND min_score > 0 AND min_score <= 100 THEN 1 ELSE 0 END) as with_score
           FROM positions GROUP BY year ORDER BY year"""
    ).fetchall()
    for y in years:
        pct = (y['with_score'] / y['total'] * 100) if y['total'] > 0 else 0
        bar = '█' * int(pct / 5) + '░' * (20 - int(pct / 5))
        print(f"  {y['year']}年: {y['with_score']:>5}/{y['total']:<5} ({pct:5.1f}%) {bar}")

    conn.close()
    print("\n✅ 清理完成！")


if __name__ == '__main__':
    dry_run = '--apply' not in sys.argv
    if dry_run:
        print("💡 提示：使用 --apply 参数执行实际清理\n")
    clean_scores(dry_run=dry_run)
