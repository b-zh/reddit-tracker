import os
import sys
import time
import requests

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

SUBREDDITS = ["watchexchange", "watchexchangecanada", "watch_swap"]
DIRECT_REFS = ["79500", "m79500"]
MODEL_TERMS = ["black bay 36", "bb36", "blackbay 36"]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) WatchDealTracker/1.0"
}


def is_target_deal(title, body):
    title_lower = title.lower()
    body_lower = body.lower()
    full_text = f"{title_lower} {body_lower}"

    # 1. Skip Want to Buy (WTB) posts
    if "[wtb]" in title_lower or "wtb:" in title_lower:
        return False

    # 2. Match reference numbers
    if any(ref in full_text for ref in DIRECT_REFS):
        return True

    # 3. Match model terms
    if "tudor" in full_text and any(term in full_text for term in MODEL_TERMS):
        return True

    return False


def notify_discord(title, url, author, body, subreddit):
    if not DISCORD_WEBHOOK_URL:
        print("Missing DISCORD_WEBHOOK_URL environment variable.")
        return

    payload = {
        "embeds": [{
            "title": f"⌚ Tudor BB36 Match: {title[:200]}",
            "url": url,
            "description": (
                f"**Subreddit:** r/{subreddit}\n"
                f"**Author:** u/{author}\n\n"
                f"{body[:300]}..." if body else "*No post body*"
            ),
            "color": 12079663
        }]
    }
    try:
        res = requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=5)
        res.raise_for_status()
        print("Notification successfully sent to Discord!")
    except Exception as e:
        print(f"Webhook error: {e}")


def test_discord():
    """Sends a single mock alert to verify Discord webhook."""
    print("Sending test notification to Discord...")
    notify_discord(
        title="[TEST] Tudor Black Bay 36 79500 Black Dial on Bracelet",
        url="https://reddit.com/r/watchexchange",
        author="test_watch_bot",
        body="This is a test notification verifying that your Discord webhook is working properly.",
        subreddit="watchexchange"
    )


def test_historical(limit=50):
    """Scans historical posts without time filters to test parser accuracy."""
    print(f"--- Scanning last {limit} posts per subreddit for Tudor BB36 matches ---")
    total_matches = 0

    for sub in SUBREDDITS:
        print(f"\nChecking r/{sub}...")
        url = f"https://www.reddit.com/r/{sub}/new.json?limit={limit}"
        try:
            res = requests.get(url, headers=HEADERS, timeout=10)
            if res.status_code != 200:
                print(f"Failed fetching r/{sub}: HTTP {res.status_code}")
                continue

            posts = res.json().get("data", {}).get("children", [])
            sub_matches = 0

            for p in posts:
                post = p.get("data", {})
                title = post.get("title", "")
                body = post.get("selftext", "")
                post_url = f"https://reddit.com{post.get('permalink', '')}"
                author = post.get("author", "")

                if is_target_deal(title, body):
                    sub_matches += 1
                    total_matches += 1
                    print(f"  [MATCH] {title}")
                    print(f"          Author: u/{author}")
                    print(f"          URL: {post_url}\n")

            if sub_matches == 0:
                print(f"  No Tudor BB36 matches found in recent {len(posts)} posts.")

        except Exception as e:
            print(f"Error checking r/{sub}: {e}")

    print(f"\n--- Scan Complete: Found {total_matches} total matches ---")


def main():
    if "--test" in sys.argv:
        test_discord()
        return

    if "--test-history" in sys.argv:
        test_historical(limit=50)
        return

    if not DISCORD_WEBHOOK_URL:
        print("Missing DISCORD_WEBHOOK_URL environment variable.")
        return

    current_time = time.time()
    window_seconds = 900  # 15 minutes

    for sub in SUBREDDITS:
        url = f"https://www.reddit.com/r/{sub}/new.json?limit=25"
        try:
            res = requests.get(url, headers=HEADERS, timeout=10)
            if res.status_code != 200:
                print(f"Failed fetching r/{sub}: HTTP {res.status_code}")
                continue

            posts = res.json().get("data", {}).get("children", [])
            for p in posts:
                post = p.get("data", {})
                created_utc = post.get("created_utc", 0)

                if (current_time - created_utc) <= window_seconds:
                    title = post.get("title", "")
                    body = post.get("selftext", "")
                    post_url = f"https://reddit.com{post.get('permalink', '')}"
                    author = post.get("author", "")

                    if is_target_deal(title, body):
                        print(f"Match found in r/{sub}: {title}")
                        notify_discord(title, post_url, author, body, sub)

        except Exception as e:
            print(f"Error checking r/{sub}: {e}")


if __name__ == "__main__":
    main()