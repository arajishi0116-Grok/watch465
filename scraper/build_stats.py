"""議員別指標の計算とJSONファイルの生成"""

import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path

from config import MEMBERS_JSON, STATS_DIR, REQUEST_INTERVAL_SEC, SUBSTANTIVE_SPEECH_MIN_WORDS
from kokkai_api import fetch_speeches, is_excluded_role
from bills import fetch_bills_by_member, fetch_interpellations_by_member


def count_content_words(text: str) -> int:
    """簡易的な内容語カウント（句読点・記号除外後の単語数で代用）"""
    text = re.sub(r"[。、！？「」『』【】\s]", " ", text)
    words = [w for w in text.split() if len(w) > 1]
    return len(words)


def calc_stats(member: dict) -> dict:
    name = member["name"]
    print(f"  処理中: {name}")

    # 直近1年分のみ取得（全期間はStep 6で実装）
    speeches = fetch_speeches(name, from_date="2024-10-01", until_date="2025-09-30")
    valid_speeches = [s for s in speeches if not is_excluded_role(s)]
    substantive = [s for s in valid_speeches if count_content_words(s.get("speech", "")) >= SUBSTANTIVE_SPEECH_MIN_WORDS]

    # 委員会・本会議の出席率は発言ベースで近似（正確な出席簿は非公開）
    committee_speeches = [s for s in substantive if "委員会" in s.get("nameOfMeeting", "") or "調査会" in s.get("nameOfMeeting", "")]
    plenary_speeches = [s for s in substantive if "本会議" in s.get("nameOfMeeting", "")]

    # 発言のあったセッション（日付×会議名）の一意カウントで近似
    # 注: 真の出席率はAPIから取得不可。aboutページに方法論を記載
    all_sessions     = max(len(set(s.get("date","") + "§" + s.get("nameOfMeeting","") for s in substantive)), 1)
    comm_sessions    = len(set(s.get("date","") + "§" + s.get("nameOfMeeting","") for s in committee_speeches))
    plenary_sessions = len(set(s.get("date","") + "§" + s.get("nameOfMeeting","") for s in plenary_speeches))

    committee_attendance_rate = round(comm_sessions / all_sessions * 100, 1)
    committee_speech_rate = round(comm_sessions / all_sessions * 100, 1)
    plenary_attendance_rate = round(plenary_sessions / all_sessions * 100, 1)

    bills = fetch_bills_by_member(name)
    interpellations = fetch_interpellations_by_member(name)

    time.sleep(REQUEST_INTERVAL_SEC)

    return {
        "committee_attendance_rate": committee_attendance_rate,
        "committee_speech_rate": committee_speech_rate,
        "plenary_attendance_rate": plenary_attendance_rate,
        "interpellations": interpellations,
        **bills,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }


def build_stats_for_members(members: list[dict]):
    stats_dir = Path(STATS_DIR)
    stats_dir.mkdir(parents=True, exist_ok=True)

    for member in members:
        if member.get("is_excluded"):
            continue
        member_id = member["id"]
        out_path = stats_dir / f"{member_id}.json"
        if out_path.exists():
            print(f"  スキップ（既存）: {member['name']}")
            continue
        try:
            stats = calc_stats(member)
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(stats, f, ensure_ascii=False, indent=2)
            print(f"  保存: {out_path}")
        except Exception as e:
            print(f"  エラー ({member['name']}): {e}")


if __name__ == "__main__":
    with open(MEMBERS_JSON, encoding="utf-8") as f:
        members = json.load(f)

    # テスト実行: 最初の1人だけ
    sample = [m for m in members if m["name"] == "岸田文雄"]
    if not sample:
        sample = members[:1]

    print(f"指標計算テスト: {sample[0]['name']}")
    build_stats_for_members(sample)
