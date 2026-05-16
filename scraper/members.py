"""衆議院公式サイトから議員マスタを取得する"""

import json
import time
import re
import httpx
from bs4 import BeautifulSoup
from pathlib import Path
from config import MEMBERS_JSON, REQUEST_INTERVAL_SEC

BASE_URL = "https://www.shugiin.go.jp/internet/itdb_annai.nsf/html/statics/syu/"
# あ行〜わ行の10ページ
PAGE_FILES = [f"{i}giin.htm" for i in range(1, 11)]

HEADERS = {"User-Agent": "WATCH465/1.0 (non-profit research, official data only)"}


def fetch_members_from_page(url: str) -> list[dict]:
    resp = httpx.get(url, headers=HEADERS, timeout=30, follow_redirects=True)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.content, "html.parser", from_encoding="shift_jis")

    members = []
    # table[1] が議員テーブル（table[0]は日付表示）
    tables = soup.find_all("table")
    if len(tables) < 2:
        return members

    for row in tables[1].find_all("tr"):
        cells = row.find_all("td")
        if len(cells) < 5:
            continue
        name = cells[0].get_text(strip=True)
        if not name or "氏名" in name:  # ヘッダー行を除外
            continue

        # 議員IDはリンクのhrefから抽出
        link = cells[0].find("a")
        member_id = ""
        if link and link.get("href"):
            m = re.search(r"(\d{6,})", link["href"])
            if m:
                member_id = m.group(1)

        # 名前末尾の「君」を除去
        name = name.rstrip("君")

        try:
            term_count = int(cells[4].get_text(strip=True))
        except ValueError:
            term_count = 0

        members.append({
            "id": member_id,
            "name": name,
            "name_kana": cells[1].get_text(strip=True).replace("　", "").replace("\n", ""),
            "party": cells[2].get_text(strip=True),
            "constituency": cells[3].get_text(strip=True),
            "constituency_type": "",  # このページには選挙区種別なし（別途取得要）
            "term_count": term_count,
            "current_term_start": "",
            "committees": [],
            "is_excluded": False,
        })

    return members


def fetch_members() -> list[dict]:
    all_members = []
    for page_file in PAGE_FILES:
        url = BASE_URL + page_file
        print(f"  取得: {page_file}")
        try:
            page_members = fetch_members_from_page(url)
            all_members.extend(page_members)
            print(f"    {len(page_members)}人")
        except Exception as e:
            print(f"    エラー: {e}")
        time.sleep(REQUEST_INTERVAL_SEC)
    return all_members


def save_members(members: list[dict]):
    path = Path(MEMBERS_JSON)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(members, f, ensure_ascii=False, indent=2)
    print(f"保存完了: {path} ({len(members)}人)")


if __name__ == "__main__":
    print("議員一覧を取得中（全10ページ）...")
    members = fetch_members()
    print(f"\n合計: {len(members)}人")
    save_members(members)
    if members:
        print("\nサンプル3件:")
        for m in members[:3]:
            print(f"  {m['name']} ({m['name_kana']}) / {m['party']} / {m['constituency']} / {m['term_count']}期")
