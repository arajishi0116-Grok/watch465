"""
speeches/ キャッシュから指標を計算して stats/ と stats_prev/ に保存する。
APIへのアクセスは不要。fetch_speeches.py でキャッシュ後に実行する。

発言カウントの定義:
  「委員会・審査会・本会議など会議単位で、実質発言が1回以上あれば1カウント」
  同一会議内で何回やりとりしてもカウントは1。
  1日に2つの委員会で発言したら2カウント。

用途:
  python build_stats.py          # 現任期・前任期を両方生成
  python build_stats.py --force  # 既存statsも上書き
"""
import json
import sys
import re
import argparse
from datetime import datetime, timezone, date
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

from config import (
    MEMBERS_JSON, SPEECHES_DIR, STATS_DIR, STATS_PREV_DIR, DATA_DIR,
    SUBSTANTIVE_SPEECH_MIN_WORDS,
    CHAMBER_SHUGIIN, CHAMBER_SANGIIN,
    CURRENT_TERM_START, PREV_TERM_START, PREV_TERM_END,
)
from kokkai_api import is_excluded_role
from fetch_speeches import load_speeches


def load_bills_index(path_name: str = "bills_index.json") -> dict:
    """bills_index.json を読み込む。なければ空dict。"""
    path = Path(DATA_DIR) / path_name
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


def count_content_words(text: str) -> int:
    """実質発言の判定（句読点等除去後の単語数）"""
    text = re.sub(r"[。、！？「」『』【】\s]", " ", text)
    return len([w for w in text.split() if len(w) > 1])


def is_substantive(speech: dict) -> bool:
    """実質的な発言かどうか（挨拶・やじ・つなぎを除外）"""
    text = speech.get("speech", "")
    return count_content_words(text) >= SUBSTANTIVE_SPEECH_MIN_WORDS


def filter_by_period(speeches: list[dict], from_date: str, until_date: str) -> list[dict]:
    return [s for s in speeches if from_date <= s.get("date", "") <= until_date]


def calc_stats(member_id: str, chamber: str, from_date: str, until_date: str) -> dict | None:
    """
    speeches キャッシュから指標を計算する。
    発言カウント = 実質発言のあった会議の数（date × nameOfMeeting のユニーク数）
    """
    speeches = load_speeches(member_id, chamber)
    if not speeches:
        return None

    # 期間フィルタ
    speeches = filter_by_period(speeches, from_date, until_date)

    # 役割除外（議長・大臣等）
    speeches = [s for s in speeches if not is_excluded_role(s)]

    # 実質発言のみ
    substantive = [s for s in speeches if is_substantive(s)]
    if not substantive:
        return None

    # ── 会議単位でカウント ──────────────────────────────────────────
    # 同一会議内で何回発言してもカウント1。異なる会議なら別カウント。
    all_meetings    = set((s.get("date", ""), s.get("nameOfMeeting", "")) for s in substantive)
    comm_meetings   = set(m for m in all_meetings
                          if "委員会" in m[1] or "調査会" in m[1])
    plenary_meetings = set(m for m in all_meetings if "本会議" in m[1])

    return {
        "speech_count":          len(all_meetings),
        "committee_speech_count": len(comm_meetings),
        "plenary_speech_count":  len(plenary_meetings),
        "interpellations": 0,       # 別途集計
        "bills_sponsored": 0,
        "bills_sponsored_passed": 0,
        "bills_sponsored_pending": 0,
        "bills_cosponsored": 0,
        "from_date": from_date,
        "until_date": until_date,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }


def build_for_period(members: list[dict], chamber: str,
                     from_date: str, until_date: str,
                     out_dir: Path, bills_index: dict,
                     force: bool):
    """指定期間の stats を out_dir に書き出す"""
    out_dir.mkdir(parents=True, exist_ok=True)
    done = skipped = 0

    for m in members:
        member_id = m["id"]
        out_path = out_dir / f"{member_id}.json"

        if not force and out_path.exists():
            skipped += 1
            continue

        stats = calc_stats(member_id, chamber, from_date, until_date)
        if stats is None:
            stats = {
                "speech_count": 0,
                "committee_speech_count": 0,
                "plenary_speech_count": 0,
                "interpellations": 0,
                "from_date": from_date,
                "until_date": until_date,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }

        stats.update(calc_bill_stats(member_id, bills_index))

        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
        done += 1

    return done, skipped


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--chamber", default=CHAMBER_SHUGIIN)
    parser.add_argument("--members", default=MEMBERS_JSON)
    parser.add_argument("--force", action="store_true", help="既存statsも上書き")
    args = parser.parse_args()

    with open(args.members, encoding="utf-8") as f:
        members = json.load(f)

    target = [m for m in members if not m.get("is_excluded") and m.get("id")]

    # 現任期の法案データ（bills_index.json = 第221回〜）
    bills_current = load_bills_index("bills_index.json")
    # 前任期の法案データ（bills_index_prev.json = 第215〜219回）
    bills_prev    = load_bills_index("bills_index_prev.json")

    today = date.today().isoformat()

    # ── 現任期 ────────────────────────────────────────────────────────
    print(f"\n【現任期】{CURRENT_TERM_START} 〜 {today}", flush=True)
    print(f"bills_index: {len(bills_current)}人分", flush=True)
    done, skipped = build_for_period(
        target, args.chamber,
        CURRENT_TERM_START, today,
        Path(STATS_DIR), bills_current, args.force
    )
    print(f"完了: {done}人更新 / {skipped}人スキップ", flush=True)

    # ── 前任期 ────────────────────────────────────────────────────────
    print(f"\n【前任期】{PREV_TERM_START} 〜 {PREV_TERM_END}", flush=True)
    print(f"bills_index_prev: {len(bills_prev)}人分", flush=True)
    done, skipped = build_for_period(
        target, args.chamber,
        PREV_TERM_START, PREV_TERM_END,
        Path(STATS_PREV_DIR), bills_prev, args.force
    )
    print(f"完了: {done}人更新 / {skipped}人スキップ", flush=True)


if __name__ == "__main__":
    main()
