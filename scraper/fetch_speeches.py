"""
議員の発言データを国会会議録APIから取得し、ローカルにキャッシュする。

保存先: ../data/speeches/{chamber}/{member_id}.json
{
  "member_id": "逢沢一郎",
  "chamber": "shugiin",
  "fetched_at": "2025-05-16T10:00:00Z",
  "from_date": "2000-01-01",
  "speech_count": 1234,
  "speeches": [ {APIレスポンスそのまま}, ... ]
}

- 既存ファイルが7日以内なら再取得しない（週次更新に最適化）
- 強制再取得したい場合は --force オプション
"""
import json
import sys
import argparse
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

from config import (
    MEMBERS_JSON, SPEECHES_DIR, REQUEST_INTERVAL_SEC,
    SPEECHES_FROM_DATE, CHAMBER_SHUGIIN, CHAMBER_SANGIIN
)
from kokkai_api import fetch_speeches, is_excluded_role

CACHE_TTL_DAYS = 7  # キャッシュ有効期限


def speeches_path(member_id: str, chamber: str) -> Path:
    return Path(SPEECHES_DIR) / chamber / f"{member_id}.json"


def is_cache_fresh(path: Path) -> bool:
    """キャッシュが有効期限内かどうか"""
    if not path.exists():
        return False
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        fetched_at = datetime.fromisoformat(data.get("fetched_at", "2000-01-01"))
        if fetched_at.tzinfo is None:
            fetched_at = fetched_at.replace(tzinfo=timezone.utc)
        age = datetime.now(timezone.utc) - fetched_at
        return age < timedelta(days=CACHE_TTL_DAYS)
    except Exception:
        return False


def fetch_and_cache(member: dict, chamber: str, force: bool = False) -> bool:
    """1議員の発言を取得してキャッシュに保存。Trueなら取得済み/成功。"""
    member_id = member["id"]
    name = member["name"].replace("　", "").replace(" ", "")
    path = speeches_path(member_id, chamber)

    if not force and is_cache_fresh(path):
        return True  # キャッシュ有効、スキップ

    try:
        until_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        speeches = fetch_speeches(name, from_date=SPEECHES_FROM_DATE, until_date=until_date)

        payload = {
            "member_id": member_id,
            "name": name,
            "chamber": chamber,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "from_date": SPEECHES_FROM_DATE,
            "until_date": until_date,
            "speech_count": len(speeches),
            "speeches": speeches,
        }

        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False)  # インデントなしで軽量化

        return True

    except Exception as e:
        print(f"  エラー ({name}): {e}", flush=True)
        return False


def load_speeches(member_id: str, chamber: str) -> list[dict]:
    """キャッシュから発言データを読み込む。ない場合は空リスト。"""
    path = speeches_path(member_id, chamber)
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return data.get("speeches", [])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--chamber", default=CHAMBER_SHUGIIN, choices=[CHAMBER_SHUGIIN, CHAMBER_SANGIIN])
    parser.add_argument("--members", default=MEMBERS_JSON, help="議員一覧JSONパス")
    parser.add_argument("--force", action="store_true", help="キャッシュを無視して再取得")
    args = parser.parse_args()

    with open(args.members, encoding="utf-8") as f:
        members = json.load(f)

    target = [m for m in members if not m.get("is_excluded") and m.get("id")]
    speeches_dir = Path(SPEECHES_DIR) / args.chamber
    cached = len(list(speeches_dir.glob("*.json"))) if speeches_dir.exists() else 0

    print(f"対象: {len(target)}人 / キャッシュ済み: {cached}人", flush=True)
    print(f"取得期間: {SPEECHES_FROM_DATE} 〜 今日\n", flush=True)

    errors = []
    for i, m in enumerate(target):
        name = m["name"].replace("　", "")
        path = speeches_path(m["id"], args.chamber)

        if not args.force and is_cache_fresh(path):
            continue

        print(f"[{i+1}/{len(target)}] {name} ({m['party']})", flush=True)
        ok = fetch_and_cache(m, args.chamber, force=args.force)
        if not ok:
            errors.append(name)
        time.sleep(REQUEST_INTERVAL_SEC)

    cached_now = len(list((Path(SPEECHES_DIR) / args.chamber).glob("*.json")))
    print(f"\n完了: {cached_now}/{len(target)}人キャッシュ済み", flush=True)
    if errors:
        print(f"エラー ({len(errors)}件): {', '.join(errors)}", flush=True)


if __name__ == "__main__":
    main()
