"""国会会議録APIクライアント"""

import time
import requests
from config import KOKKAI_API_BASE, REQUEST_INTERVAL_SEC, MAX_RECORDS_PER_REQUEST, EXCLUDED_SPEAKER_ROLES


def fetch_speeches(speaker: str, from_date: str = None, until_date: str = None) -> list[dict]:
    """
    指定議員の発言一覧を全件取得する。
    speaker: 発言者名（例: "岸田文雄"）
    from_date / until_date: "YYYY-MM-DD" 形式（省略可）
    """
    speeches = []
    start = 1

    while True:
        params = {
            "speaker": speaker,
            "startRecord": start,
            "maximumRecords": MAX_RECORDS_PER_REQUEST,
            "recordPacking": "json",
        }
        if from_date:
            params["from"] = from_date
        if until_date:
            params["until"] = until_date

        resp = requests.get(KOKKAI_API_BASE, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        results = data.get("speechRecord", [])
        speeches.extend(results)

        total = int(data.get("numberOfRecords", 0))
        if start + MAX_RECORDS_PER_REQUEST - 1 >= total:
            break

        start += MAX_RECORDS_PER_REQUEST
        time.sleep(REQUEST_INTERVAL_SEC)

    return speeches


def is_excluded_role(speech: dict) -> bool:
    """発言者役割が除外対象かどうか判定する"""
    role = speech.get("speakerRole") or ""
    return any(r in role for r in EXCLUDED_SPEAKER_ROLES)


if __name__ == "__main__":
    # 接続テスト
    import json
    name = "岸田文雄"
    print(f"{name} の発言データを取得中...")
    speeches = fetch_speeches(name, from_date="2024-01-01", until_date="2024-03-31")
    valid = [s for s in speeches if not is_excluded_role(s)]
    print(f"  総発言数: {len(speeches)}")
    print(f"  役割除外後: {len(valid)}")
    if valid:
        sample = valid[0]
        print(f"  サンプル: [{sample.get('date')}] {sample.get('nameOfHouse')} - {sample.get('nameOfMeeting')}")
        print(f"  発言冒頭: {sample.get('speech', '')[:80]}...")
