"""
週次更新メインスクリプト。
1. fetch_speeches.py  -- APIから発言データを取得してキャッシュ
2. build_stats.py     -- キャッシュから指標を計算

使い方:
  python fetch_all.py              # 通常の週次更新
  python fetch_all.py --force      # キャッシュを無視して全件再取得
  python fetch_all.py --stats-only # 指標計算のみ（API不使用）
"""
import sys
import argparse
import subprocess

sys.stdout.reconfigure(encoding="utf-8")


def run(cmd: list[str]):
    result = subprocess.run(cmd, check=True)
    return result.returncode == 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--stats-only", action="store_true", help="指標計算のみ（発言取得スキップ）")
    args = parser.parse_args()

    if not args.stats_only:
        print("=== Step 1: 発言データ取得 ===", flush=True)
        cmd = [sys.executable, "fetch_speeches.py"]
        if args.force:
            cmd.append("--force")
        run(cmd)

    print("\n=== Step 2: 指標計算 ===", flush=True)
    cmd = [sys.executable, "build_stats.py"]
    if args.force:
        cmd.append("--force")
    run(cmd)

    print("\n=== 完了 ===", flush=True)


if __name__ == "__main__":
    main()
