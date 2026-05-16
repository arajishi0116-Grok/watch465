"""
衆議院議員立法（衆法）を会期ごとに取得し、
提出者名で議員別に振り分けて bills_index.json を生成する。

生成物: ../data/bills_index.json
  { "議員名": [ {session, number, name, status, url, is_primary}, ... ] }
"""
import json, re, time, sys
from pathlib import Path
import httpx
from bs4 import BeautifulSoup

sys.stdout.reconfigure(encoding='utf-8')

BASE = "https://www.shugiin.go.jp/internet/itdb_gian.nsf/html/gian/"
HEADERS = {"User-Agent": "WATCH465/1.0 (non-profit research, official data only)"}
INTERVAL = 2  # 秒

# 対象会期（直近4会期）※新会期が始まったらここに追加する
SESSIONS = [218, 219, 220, 221]


def get_soup(url: str) -> BeautifulSoup:
    resp = httpx.get(url, headers=HEADERS, timeout=30, follow_redirects=True)
    resp.raise_for_status()
    return BeautifulSoup(resp.content, "html.parser", from_encoding="shift_jis")


def fetch_shuhou_list(session: int) -> list[dict]:
    """指定会期の衆法一覧を取得"""
    url = f"{BASE}kaiji{session}.htm"
    try:
        soup = get_soup(url)
    except Exception as e:
        print(f"  会期{session}取得失敗: {e}")
        return []

    bills = []
    # 衆法テーブルを探す（id='05' セクション以降のテーブル）
    section = soup.find(id="05") or soup.find("a", attrs={"name": "05"})
    if not section:
        return []

    # セクション以降のテーブルを取得（閣法等が混じらないよう衆法のみ）
    for table in soup.find_all("table"):
        rows = table.find_all("tr")
        for row in rows:
            cells = row.find_all("td")
            if len(cells) < 4:
                continue
            # 会期番号チェック
            cell0 = cells[0].get_text(strip=True)
            if str(session) not in cell0 and cell0 not in ("", str(session)):
                # 継続案件は前会期番号が入ることも
                pass

            # 法案名（3列目）と経過リンク
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

            if keika_link:
                full_url = BASE + keika_link.lstrip("./")
                bills.append({
                    "session": session,
                    "name": name,
                    "status": status,
                    "keika_url": full_url,
                })

    return bills


def fetch_proposer(keika_url: str) -> tuple[str, str]:
    """経過ページから提出者と提出会派を取得"""
    try:
        soup = get_soup(keika_url)
        text = soup.get_text()
        # 「議案提出者」行を探す
        m = re.search(r"議案提出者\s+(.+?)(?:\n|議案提出会派)", text)
        proposer = m.group(1).strip() if m else ""
        # 「議案提出会派」行
        m2 = re.search(r"議案提出会派\s+(.+?)(?:\n|衆議院)", text)
        faction = m2.group(1).strip() if m2 else ""
        return proposer, faction
    except Exception:
        return "", ""


def normalize_name(raw: str) -> str:
    """「山田　太郎君外X名」→「山田太郎」"""
    raw = re.sub(r'君外[一二三四五六七八九十百千万\d]+名.*', '', raw)
    raw = re.sub(r'君$', '', raw)
    raw = raw.replace('　', '').replace(' ', '').strip()
    return raw


def build_index():
    index: dict[str, list] = {}
    total_bills = 0

    for session in SESSIONS:
        print(f"\n第{session}回国会 衆法を取得中...")
        bills = fetch_shuhou_list(session)
        print(f"  {len(bills)}件")
        time.sleep(INTERVAL)

        for i, bill in enumerate(bills):
            print(f"  [{i+1}/{len(bills)}] {bill['name'][:30]}")
            proposer_raw, faction = fetch_proposer(bill["keika_url"])
            proposer_name = normalize_name(proposer_raw)

            if not proposer_name:
                time.sleep(INTERVAL)
                continue

            entry = {
                "session": session,
                "name": bill["name"],
                "status": bill["status"],
                "url": bill["keika_url"],
                "is_primary": True,
                "faction": faction,
            }

            if proposer_name not in index:
                index[proposer_name] = []
            index[proposer_name].append(entry)
            total_bills += 1
            time.sleep(INTERVAL)

    out = Path("../data/bills_index.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)

    print(f"\n完了: {total_bills}件 / {len(index)}人分")
    print(f"保存: {out}")


if __name__ == "__main__":
    build_index()
