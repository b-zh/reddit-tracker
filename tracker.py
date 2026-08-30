import os
import sys
import time
import feedparser
import requests

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

# Combined multireddit feed URL
FEED_URL = "https://www.reddit.com/r/watchexchange+watchexchangecanada+watch_swap/new/.rss?sort=new"

# Add terms here to test standalone words (e.g., "seiko", "omega")
DIRECT_REFS = ["79500", "m79500"]
MODEL_TERMS = ["black bay 36", "bb36", "blackbay 36", "smiley"]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}


def is_target_deal(title, body):
    title_lower = title.lower()
    body_lower = body.lower()
    full_text = f"{title_lower} {body_lower}"

    if "[wtb]" in title_lower or "wtb:" in title_lower:
        return False

    # Matches direct references or standalone test keywords
    if any(ref in full_text for ref in DIRECT_REFS):
        return True

    # Matches Tudor model variants
    if "tudor" in full_text and any(term in full_text for term in MODEL_TERMS):
        return True

    return False


def notify_discord(title, url, author, body):
    if not DISCORD_WEBHOOK_URL:
        print("Missing DISCORD_WEBHOOK_URL environment variable.")
        return

    payload = {
        "embeds": [{
            "title": f"⌚ Match Found: {title[:200]}",
            "url": url,
            "description": (
                f"**Author:** {author}\n\n"
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
    print("Sending test notification to Discord...")
    notify_discord(
        title="[TEST] Tudor Black Bay 36 79500 Black Dial on Bracelet",
        url="https://reddit.com/r/watchexchange",
        author="u/test_watch_bot",
        body="This is a test notification verifying that your Discord webhook is working properly."
    )


def test_historical():
    print("--- Scanning latest posts via RSS ---")
    try:
        res = requests.get(FEED_URL, headers=HEADERS, timeout=10)
        feed = feedparser.parse(res.content)
        
        print(f"Fetched {len(feed.entries)} total entries across all target subreddits.\n")
        matches = 0

        for entry in feed.entries:
            title = getattr(entry, "title", "")
            body = getattr(entry, "summary", "")
            post_url = getattr(entry, "link", "")
            author = getattr(entry, "author", "unknown")

            if is_target_deal(title, body):
                matches += 1
                print(f"  [MATCH] {title}")
                print(f"          Author: {author}")
                print(f"          URL: {post_url}\n")

        print(f"--- Scan Complete: Found {matches} matches ---")

    except Exception as e:
        print(f"Error fetching feed: {e}")


def main():
    if "--test" in sys.argv:
        test_discord()
        return

    if "--test-history" in sys.argv:
        test_historical()
        return

    if not DISCORD_WEBHOOK_URL:
        print("Missing DISCORD_WEBHOOK_URL environment variable.")
        return

    current_time = time.time()
    window_seconds = 900  # 15 minutes

    try:
        res = requests.get(FEED_URL, headers=HEADERS, timeout=10)
        feed = feedparser.parse(res.content)

        for entry in feed.entries:
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                published_utc = time.mktime(entry.published_parsed)
            else:
                published_utc = current_time

            if (current_time - published_utc) <= window_seconds:
                title = getattr(entry, "title", "")
                body = getattr(entry, "summary", "")
                post_url = getattr(entry, "link", "")
                author = getattr(entry, "author", "unknown")

                if is_target_deal(title, body):
                    print(f"Match found: {title}")
                    notify_discord(title, post_url, author, body)

    except Exception as e:
        print(f"Error checking feed: {e}")


if __name__ == "__main__":
    main()