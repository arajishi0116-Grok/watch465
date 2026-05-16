"""
全465議員のデータ取得スクリプト。
- 既にstats/{id}.jsonが存在する場合はスキップ（中断再開可能）
- レート制限: 3秒間隔
- 進捗をコンソールに逐次出力
"""
import sys, json, re, time
sys.stdout.reconfigure(encoding='utf-8')

from datetime import datetime, timezone
from pathlib import Path

from kokkai_api import fetch_speeches, is_excluded_role
from config import (
    MEMBERS_JSON, STATS_DIR, REQUEST_INTERVAL_SEC,
    SUBSTANTIVE_SPEECH_MIN_WORDS
)

# 取得対象期間（直近1年: 第215回〜216回国会）
FROM_DATE = "2024-10-01"
UNTIL_DATE = "2025-09-30"


def count_content_words(text: str) -> int:
    text = re.sub(r"[。、！？「」『』【】\s]", " ", text)
    return len([w for w in text.split() if len(w) > 1])


def calc_and_save(member: dict) -> bool:
    """指標を計算してstats/{id}.jsonに保存。成功したらTrueを返す"""
    member_id = member["id"]
    name = member["name"]
    out_path = Path(STATS_DIR) / f"{member_id}.json"

    if out_path.exists():
        return True  # スキップ

    try:
        speeches = fetch_speeches(name, from_date=FROM_DATE, until_date=UNTIL_DATE)
        valid = [s for s in speeches if not is_excluded_role(s)]
        substantive = [s for s in valid if count_content_words(s.get("speech", "")) >= SUBSTANTIVE_SPEECH_MIN_WORDS]

        committee = [s for s in substantive if "委員会" in s.get("nameOfMeeting", "") or "調査会" in s.get("nameOfMeeting", "")]
        plenary = [s for s in substantive if "本会議" in s.get("nameOfMeeting", "")]

        all_sessions = max(len(set(s.get("date","") + "§" + s.get("nameOfMeeting","") for s in substantive)), 1)
        comm_sessions = len(set(s.get("date","") + "§" + s.get("nameOfMeeting","") for s in committee))
        plen_sessions = len(set(s.get("date","") + "§" + s.get("nameOfMeeting","") for s in plenary))

        stats = {
            "committee_attendance_rate": round(comm_sessions / all_sessions * 100, 1),
            "committee_speech_rate": round(comm_sessions / all_sessions * 100, 1),
            "plenary_attendance_rate": round(plen_sessions / all_sessions * 100, 1),
            "interpellations": 0,        # 将来実装
            "bills_sponsored": 0,
            "bills_sponsored_passed": 0,
            "bills_sponsored_pending": 0,
            "bills_cosponsored": 0,
            "speech_count": len(substantive),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
        return True

    except Exception as e:
        print(f"  エラー: {e}", flush=True)
        return False


def main():
    with open(MEMBERS_JSON, encoding="utf-8") as f:
        members = json.load(f)

    stats_dir = Path(STATS_DIR)
    done = len(list(stats_dir.glob("*.json"))) if stats_dir.exists() else 0
    total = len([m for m in members if not m.get("is_excluded") and m.get("id")])

    print(f"対象: {total}人 / 既完了: {done}人", flush=True)
    errors = []

    for i, m in enumerate(members):
        if m.get("is_excluded") or not m.get("id"):
            continue
        out_path = Path(STATS_DIR) / f"{m['id']}.json"
        if out_path.exists():
            continue

        name = m["name"].replace("　", "")
        print(f"[{i+1}/{len(members)}] {name} ({m['party']})", flush=True)

        ok = calc_and_save(m)
        if not ok:
            errors.append(name)

        time.sleep(REQUEST_INTERVAL_SEC)

    done_now = len(list(stats_dir.glob("*.json"))) if stats_dir.exists() else 0
    print(f"\n完了: {done_now}/{total}人", flush=True)
    if errors:
        print(f"エラー ({len(errors)}件): {', '.join(errors)}", flush=True)


if __name__ == "__main__":
    main()
