"""
データ更新後にXへ自動投稿する。
環境変数: X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_TOKEN_SECRET
"""
import os
import sys
import json
import datetime
from pathlib import Path

try:
    import tweepy
except ImportError:
    print("tweepy not installed, skipping X post")
    sys.exit(0)

def count_stats():
    stats_dir = Path("../data/stats")
    if not stats_dir.exists():
        return 0
    return len(list(stats_dir.glob("*.json")))

def post():
    api_key = os.environ.get("X_API_KEY")
    api_secret = os.environ.get("X_API_SECRET")
    access_token = os.environ.get("X_ACCESS_TOKEN")
    access_secret = os.environ.get("X_ACCESS_TOKEN_SECRET")
    site_url = os.environ.get("SITE_URL", "https://watch465.vercel.app")

    if not all([api_key, api_secret, access_token, access_secret]):
        print("X API credentials not set, skipping")
        return

    client = tweepy.Client(
        consumer_key=api_key,
        consumer_secret=api_secret,
        access_token=access_token,
        access_token_secret=access_secret,
    )

    today = datetime.date.today().strftime("%Y年%m月%d日")
    count = count_stats()

    text = (
        f"【週次更新】Watch465 データを更新しました（{today}）\n\n"
        f"衆議院議員{count}人分の国会活動記録（委員会発言率・質問主意書・立法件数など）を公開中です。\n"
        f"あなたの選挙区選出議員の活動を確認してください。\n\n"
        f"{site_url}\n\n"
        f"#国会 #衆議院 #政治 #Watch465"
    )

    try:
        response = client.create_tweet(text=text)
        print(f"X投稿完了: tweet_id={response.data['id']}")
    except Exception as e:
        print(f"X投稿失敗: {e}")
        sys.exit(1)

if __name__ == "__main__":
    post()
