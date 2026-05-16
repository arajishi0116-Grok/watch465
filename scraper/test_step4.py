"""Step 4テスト: 発言APIのみで指標計算（bills/interpellationsは除く）"""
import sys, json, re
sys.stdout.reconfigure(encoding='utf-8')
from datetime import datetime
from pathlib import Path
from kokkai_api import fetch_speeches, is_excluded_role
from config import SUBSTANTIVE_SPEECH_MIN_WORDS, STATS_DIR

def count_content_words(text: str) -> int:
    text = re.sub(r"[。、！？「」『』【】\s]", " ", text)
    return len([w for w in text.split() if len(w) > 1])

def calc_stats_api_only(name: str, member_id: str) -> dict:
    print(f"発言データ取得: {name} (2024-10-01〜2025-09-30)")
    speeches = fetch_speeches(name, from_date="2024-10-01", until_date="2025-09-30")
    print(f"  取得件数: {len(speeches)}")

    valid = [s for s in speeches if not is_excluded_role(s)]
    substantive = [s for s in valid if count_content_words(s.get("speech", "")) >= SUBSTANTIVE_SPEECH_MIN_WORDS]
    print(f"  役割除外後: {len(valid)}, 実質発言: {len(substantive)}")

    committee = [s for s in substantive if "委員会" in s.get("nameOfMeeting", "") or "調査会" in s.get("nameOfMeeting", "")]
    plenary = [s for s in substantive if "本会議" in s.get("nameOfMeeting", "")]

    # 発言のあった会議セッション（日付×会議名）を一意にカウント
    all_sessions     = len(set(s.get("date","") + "§" + s.get("nameOfMeeting","") for s in substantive))
    comm_sessions    = len(set(s.get("date","") + "§" + s.get("nameOfMeeting","") for s in committee))
    plenary_sessions = len(set(s.get("date","") + "§" + s.get("nameOfMeeting","") for s in plenary))
    total_sessions   = max(all_sessions, 1)

    # 注: 真の出席率は取得不可のため「発言セッション比率」で近似（aboutページに記載）
    stats = {
        "committee_attendance_rate": round(comm_sessions / total_sessions * 100, 1),
        "committee_speech_rate": round(comm_sessions / total_sessions * 100, 1),
        "plenary_attendance_rate": round(plenary_sessions / total_sessions * 100, 1),
        "interpellations": 0,   # Step 6で実装
        "bills_sponsored": 0,
        "bills_sponsored_passed": 0,
        "bills_sponsored_pending": 0,
        "bills_cosponsored": 0,
        "updated_at": datetime.utcnow().isoformat() + "Z",
    }

    out = Path(STATS_DIR) / f"{member_id}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

    return stats

if __name__ == "__main__":
    # members.jsonから最初の非除外議員を使用
    with open("../data/members.json", encoding="utf-8") as f:
        members = json.load(f)

    # 岸田文雄を優先、なければ先頭
    sample = next((m for m in members if m["name"].replace("　", "") == "岸田文雄"), members[0])
    print(f"テスト対象: {sample['name']} / {sample['party']} / {sample['constituency']}")

    stats = calc_stats_api_only(sample["name"], sample["id"] or "test")
    print("\n指標結果:")
    for k, v in stats.items():
        print(f"  {k}: {v}")
