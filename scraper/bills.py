"""議員立法・質問主意書データの取得"""

import time
import re
import httpx
from bs4 import BeautifulSoup
from config import REQUEST_INTERVAL_SEC

BILLS_URL = "https://www.shugiin.go.jp/internet/itdb_gian.nsf/html/gian/menu.htm"
INTERPELLATIONS_URL = "https://www.shugiin.go.jp/internet/itdb_shitsumon.nsf/html/shitsumon/menu.htm"

HEADERS = {"User-Agent": "WATCH465/1.0 (non-profit research, official data only)"}


def fetch_bills_by_member(member_name: str) -> dict:
    """指定議員の議員立法件数（主提案・共同提案）を返す"""
    resp = httpx.get(BILLS_URL, headers=HEADERS, timeout=30, follow_redirects=True)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    sponsored = 0
    sponsored_passed = 0
    sponsored_pending = 0
    cosponsored = 0

    for row in soup.select("table tr"):
        cells = row.find_all("td")
        text = " ".join(c.get_text(strip=True) for c in cells)
        if member_name not in text:
            continue
        # 主提案判定: 発議者欄に単独で名前がある行
        if cells and member_name == cells[0].get_text(strip=True):
            sponsored += 1
            status = cells[-1].get_text(strip=True) if cells else ""
            if "成立" in status:
                sponsored_passed += 1
            elif "審議" in status or "継続" in status:
                sponsored_pending += 1
        else:
            cosponsored += 1

    time.sleep(REQUEST_INTERVAL_SEC)

    return {
        "bills_sponsored": sponsored,
        "bills_sponsored_passed": sponsored_passed,
        "bills_sponsored_pending": sponsored_pending,
        "bills_cosponsored": cosponsored,
    }


def fetch_interpellations_by_member(member_name: str) -> int:
    """指定議員の質問主意書提出本数を返す"""
    resp = httpx.get(INTERPELLATIONS_URL, headers=HEADERS, timeout=30, follow_redirects=True)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    count = 0
    for row in soup.select("table tr"):
        cells = row.find_all("td")
        text = " ".join(c.get_text(strip=True) for c in cells)
        if member_name in text:
            count += 1

    time.sleep(REQUEST_INTERVAL_SEC)
    return count
