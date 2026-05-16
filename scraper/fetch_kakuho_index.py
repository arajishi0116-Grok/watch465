"""
内閣提出法案（閣法）を会期ごとに取得して kakuho_index.json を生成する。

生成物: ../data/kakuho_index.json
  {
    "217": [
      {
        "session": 217,
        "number": 1,
        "name": "所得税法等の一部を改正する法律案",
        "status": "成立",
        "url": "https://...",
        "committee": "財務金融委員会"   # 経過ページから取得
      },
      ...
    ],
    "216": [...],
    ...
  }

閣法は内閣提出なので議員別ではなく会期別・委員会別で管理する。
議員ページでは「所属委員会で審議した閣法」として表示する。
"""
import json, re, time, sys
from pathlib import Path
import httpx
from bs4 import BeautifulSoup

sys.stdout.reconfigure(encoding='utf-8')

BASE = "https://www.shugiin.go.jp/internet/itdb_gian.nsf/html/gian/"
HEADERS = {"User-Agent": "WATCH465/1.0 (non-profit research, official data only)"}
INTERVAL = 2

# 対象会期（現任期：2024年10月衆院選以降）※新会期が始まったらここに追加する
SESSIONS = [221]  # 現任期：第51回衆院選後（2026年2月〜）

# 衆法(継続)=05, 衆法(今会期)=06, 閣法=09
KAKUHO_ANCHOR = "09"


def get_soup(url: str) -> BeautifulSoup:
    resp = httpx.get(url, headers=HEADERS, timeout=30, follow_redirects=True)
    resp.raise_for_status()
    return BeautifulSoup(resp.content, "html.parser", from_encoding="shift_jis")


def fetch_kakuho_list(session: int) -> list[dict]:
    """指定会期の閣法一覧を取得"""
    url = f"{BASE}kaiji{session}.htm"
    try:
        soup = get_soup(url)
    except Exception as e:
        print(f"  会期{session}取得失敗: {e}")
        return []

    section = soup.find("a", attrs={"name": KAKUHO_ANCHOR})
    if not section:
        print(f"  会期{session}: 閣法セクションなし")
        return []

    tbl = section.find_next("table")
    if not tbl:
        return []

    bills = []
    for row in tbl.find_all("tr"):
        cells = row.find_all("td")
        if len(cells) < 4:
            continue
        name = cells[2].get_text(strip=True) if len(cells) > 2 else ""
        status = cells[3].get_text(strip=True) if len(cells) > 3 else ""
        if not name or len(name) < 4:
            continue

        # 経過リンク
        keika_link = ""
        for a in row.find_all("a", href=True):
            if "keika" in a["href"]:
                keika_link = a["href"]
                break

        bill = {
            "session": session,
            "name": name,
            "status": status,
            "url": BASE + keika_link.lstrip("./") if keika_link else "",
            "committee": "",
        }
        bills.append(bill)

    return bills


def fetch_committee(keika_url: str) -> str:
    """経過ページから審査委員会名を取得"""
    if not keika_url:
        return ""
    try:
        soup = get_soup(keika_url)
        text = soup.get_text()
        # 「委員会」を含む行を探す
        m = re.search(r"([\w・]+委員会|[\w・]+調査会)", text)
        return m.group(1) if m else ""
    except Exception:
        return ""


def build_index():
    index: dict[str, list] = {}

    for session in SESSIONS:
        print(f"\n第{session}回国会 閣法を取得中...")
        bills = fetch_kakuho_list(session)
        print(f"  {len(bills)}件")
        time.sleep(INTERVAL)

        session_bills = []
        for i, bill in enumerate(bills):
            print(f"  [{i+1}/{len(bills)}] {bill['name'][:35]}", flush=True)
            if bill["url"]:
                bill["committee"] = fetch_committee(bill["url"])
                time.sleep(INTERVAL)
            session_bills.append(bill)

        index[str(session)] = session_bills

    out = Path("../data/kakuho_index.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)

    total = sum(len(v) for v in index.values())
    print(f"\n完了: {total}件")
    print(f"保存: {out}")


if __name__ == "__main__":
    build_index()
