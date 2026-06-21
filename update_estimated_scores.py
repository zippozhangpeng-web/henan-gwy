#!/usr/bin/env python3
"""
补充 is_estimated=1 岗位的 max_score 和 avg_score

- avg_score = min_score（估算分作为均值最合理）
- max_score = min_score + random.uniform(3, 8)（上下浮动）
- 使用 position id 作为随机种子，确保结果可复现
"""
import sqlite3
import os
import random
import sys

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'gwy_data.db')


def backfill_estimated_scores(dry_run=False):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    # 查找所有 is_estimated=1 但 max_score/avg_score 缺失的岗位
    to_fix = conn.execute("""
        SELECT id, min_score, max_score, avg_score
        FROM positions
        WHERE is_estimated = 1
          AND (max_score IS NULL OR max_score = 0
               OR avg_score IS NULL OR avg_score = 0)
        ORDER BY id
    """).fetchall()

    print(f"需要补充的岗位: {len(to_fix)} 个")

    if dry_run:
        for pos in to_fix[:10]:
            random.seed(pos['id'])
            estimated_avg = round(pos['min_score'], 2)
            estimated_max = round(pos['min_score'] + random.uniform(3, 8), 2)
            print(f"  id={pos['id']}  min={pos['min_score']} → avg={estimated_avg}  max={estimated_max}")
        print(f"\n  ... (共 {len(to_fix)} 个)")
        print("\n⚠️  DRY RUN 模式：使用 --apply 执行实际写入")
        conn.close()
        return

    updated = 0
    for pos in to_fix:
        random.seed(pos['id'])
        estimated_avg = round(pos['min_score'], 2)
        estimated_max = round(pos['min_score'] + random.uniform(3, 8), 2)

        conn.execute("""
            UPDATE positions
            SET max_score = ?, avg_score = ?
            WHERE id = ?
        """, (estimated_max, estimated_avg, pos['id']))
        updated += 1

        if updated % 2000 == 0:
            conn.commit()
            print(f"  已处理 {updated}/{len(to_fix)}...")

    conn.commit()

    # 验证
    remaining = conn.execute("""
        SELECT COUNT(*) FROM positions
        WHERE is_estimated = 1
          AND (max_score IS NULL OR max_score = 0
               OR avg_score IS NULL OR avg_score = 0)
    """).fetchone()[0]

    print(f"\n✅ 已补充 {updated} 个岗位的 max_score 和 avg_score")
    print(f"   剩余缺失: {remaining} 个（应为0）")
    conn.close()


if __name__ == '__main__':
    dry_run = '--apply' not in sys.argv
    if dry_run:
        print("💡 提示：使用 --apply 执行实际写入\n")
    backfill_estimated_scores(dry_run=dry_run)
