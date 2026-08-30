import os
import time
import requests

# Only your Discord Webhook is needed
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

SUBREDDITS = ["watchexchange", "watchexchangecanada", "watch_swap"]
DIRECT_REFS = ["79500", "m79500"]
MODEL_TERMS = ["black bay 36", "bb36", "blackbay 36"]

HEADERS = {
    # Custom User-Agent prevents Reddit from rate-limiting public RSS requests
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
        requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=5)
    except Exception as e:
        print(f"Webhook error: {e}")

def main():
    if not DISCORD_WEBHOOK_URL:
        print("Missing DISCORD_WEBHOOK_URL environment variable.")
        return

    current_time = time.time()
    # Check posts published in the last 15 minutes (900 seconds)
    window_seconds = 900 

    for sub in SUBREDDITS:
        url = f"https://www.reddit.com/r/{sub}/new.json?limit=25"
        try:
            response = requests.get(url, headers=HEADERS, timeout=10)
            if response.status_code != 200:
                print(f"Failed fetching r/{sub}: HTTP {response.status_code}")
                continue

            data = response.json()
            posts = data.get("data", {}).get("children", [])

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