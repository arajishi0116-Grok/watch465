"""
speeches/ キャッシュから指標を計算して stats/ に保存する。
APIへのアクセスは不要。fetch_speeches.py でキャッシュ後に実行する。

用途:
  python build_stats.py                    # 全員（shugiin）
  python build_stats.py --force            # 既存statsも上書き
  python build_stats.py --chamber sangiin  # 参議院（将来）
  python build_stats.py --from 2025-03-01 --until 2025-12-31  # 期間指定
"""
import json
import sys
import re
import argparse
from datetime import datetime, timezone, date
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

from config import (
    MEMBERS_JSON, SPEECHES_DIR, STATS_DIR, DATA_DIR,
    SUBSTANTIVE_SPEECH_MIN_WORDS,
    CHAMBER_SHUGIIN, CHAMBER_SANGIIN,
    SPEECHES_FROM_DATE,
)
from kokkai_api import is_excluded_role
from fetch_speeches import load_speeches


def load_bills_index() -> dict:
    """bills_index.json を読み込む。なければ空dict。"""
    path = Path(DATA_DIR) / "bills_index.json"
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def calc_bill_stats(member_id: str, bills_index: dict) -> dict:
    """bills_index から主提案・成立・審議中・共同提案を集計する"""
    bills = bills_index.get(member_id, [])
    primary = [b for b in bills if b.get("is_primary", True)]
    return {
        "bills_sponsored": len(primary),
        "bills_sponsored_passed": len([b for b in primary if b.get("status") == "成立"]),
        "bills_sponsored_pending": len([b for b in primary
                                        if "審議" in b.get("status", "") or "閉会" in b.get("status", "")]),
        "bills_cosponsored": len([b for b in bills if not b.get("is_primary", True)]),
    }


# 第217回国会（2025年3月〜）を対象期間とする
CURRENT_TERM_START = "2025-03-01"


def count_content_words(text: str) -> int:
    """実質発言の判定（句読点等除去後の単語数）"""
    text = re.sub(r"[。、！？「」『』【】\s]", " ", text)
    return len([w for w in text.split() if len(w) > 1])


def is_substantive(speech: dict) -> bool:
    """実質的な発言かどうか（挨拶・やじ・つなぎを除外）"""
    text = speech.get("speech", "")
    if count_content_words(text) < SUBSTANTIVE_SPEECH_MIN_WORDS:
        return False
    return True


def filter_by_period(speeches: list[dict], from_date: str, until_date: str) -> list[dict]:
    result = []
    for s in speeches:
        d = s.get("date", "")
        if d and from_date <= d <= until_date:
            result.append(s)
    return result


def calc_stats(member_id: str, chamber: str, from_date: str, until_date: str) -> dict | None:
    """speeches キャッシュから指標を計算する"""
    speeches = load_speeches(member_id, chamber)
    if not speeches:
        return None

    # 期間フィルタ
    speeches = filter_by_period(speeches, from_date, until_date)

    # 役割除外（議長・大臣等）
    speeches = [s for s in speeches if not is_excluded_role(s)]

    # 実質発言のみ
    substantive = [s for s in speeches if is_substantive(s)]

    # 委員会 / 本会議に分類
    committee = [s for s in substantive
                 if "委員会" in s.get("nameOfMeeting", "") or "調査会" in s.get("nameOfMeeting", "")]
    plenary = [s for s in substantive if "本会議" in s.get("nameOfMeeting", "")]

    return {
        "speech_count": len(substantive),
        "committee_speech_count": len(committee),
        "plenary_speech_count": len(plenary),
        "interpellations": 0,       # fetch_bills_index.py で別途集計
        "bills_sponsored": 0,
        "bills_sponsored_passed": 0,
        "bills_sponsored_pending": 0,
        "bills_cosponsored": 0,
        "from_date": from_date,
        "until_date": until_date,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--chamber", default=CHAMBER_SHUGIIN)
    parser.add_argument("--members", default=MEMBERS_JSON)
    parser.add_argument("--from", dest="from_date", default=CURRENT_TERM_START)
    parser.add_argument("--until", dest="until_date", default=date.today().isoformat())
    parser.add_argument("--force", action="store_true", help="既存statsも上書き")
    args = parser.parse_args()

    with open(args.members, encoding="utf-8") as f:
        members = json.load(f)

    target = [m for m in members if not m.get("is_excluded") and m.get("id")]
    stats_dir = Path(STATS_DIR)
    stats_dir.mkdir(parents=True, exist_ok=True)

    print(f"指標計算: {len(target)}人 / 期間 {args.from_date} 〜 {args.until_date}", flush=True)

    bills_index = load_bills_index()
    print(f"bills_index: {len(bills_index)}人分読み込み済み", flush=True)

    done = skipped = errors = 0
    for m in target:
        member_id = m["id"]
        name = m["name"].replace("　", "")
        out_path = stats_dir / f"{member_id}.json"

        if not args.force and out_path.exists():
            skipped += 1
            continue

        stats = calc_stats(member_id, args.chamber, args.from_date, args.until_date)
        if stats is None:
            # 発言データがなくても法案データだけでstatsを作る
            stats = {
                "speech_count": 0,
                "committee_speech_count": 0,
                "plenary_speech_count": 0,
                "interpellations": 0,
                "from_date": args.from_date,
                "until_date": args.until_date,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }

        # 法案データをマージ
        stats.update(calc_bill_stats(member_id, bills_index))

        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
        done += 1

    print(f"\n完了: {done}人更新 / {skipped}人スキップ / {errors}人データなし", flush=True)


if __name__ == "__main__":
    main()
