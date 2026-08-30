import os
import time
import praw
import requests

# --- Credentials from Koyeb Environment Variables ---
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT", "watch-deal-tracker:v1.0")
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

# --- Target Subreddits ---
TARGET_SUBREDDITS = "watchexchange+watchexchangecanada+watch_swap"

# Match exact reference numbers or combinations of model keywords
DIRECT_REFS = ["79500", "m79500"]
MODEL_TERMS = ["black bay 36", "bb36", "blackbay 36"]


def is_target_deal(post):
    """
    Checks if a submission matches Tudor BB36 criteria 
    and ignores Want to Buy [WTB] posts.
    """
    title_lower = post.title.lower()
    body_lower = post.selftext.lower()
    full_text = f"{title_lower} {body_lower}"

    # 1. Skip Want to Buy (WTB) requests
    if "[wtb]" in title_lower or "wtb:" in title_lower:
        return False

    # 2. Check for exact reference matches
    if any(ref in full_text for ref in DIRECT_REFS):
        return True

    # 3. Check for model name matches (e.g. Tudor + BB36)
    if "tudor" in full_text and any(term in full_text for term in MODEL_TERMS):
        return True

    return False


def notify_discord(post):
    payload = {
        "embeds": [{
            "title": f"⌚ Tudor BB36 Match: {post.title[:200]}",
            "url": post.url,
            "description": (
                f"**Subreddit:** r/{post.subreddit.display_name}\n"
                f"**Author:** u/{post.author}\n\n"
                f"{post.selftext[:300]}..." if post.selftext else "*No post body*"
            ),
            "color": 12079663  # Tudor burgundy/red accent
        }]
    }
    try:
        requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=5)
    except Exception as e:
        print(f"Webhook error: {e}")


def run_agent():
    reddit = praw.Reddit(
        client_id=REDDIT_CLIENT_ID,
        client_secret=REDDIT_CLIENT_SECRET,
        user_agent=REDDIT_USER_AGENT
    )

    subreddit = reddit.subreddit(TARGET_SUBREDDITS)
    print(f"Connected! Monitoring r/{TARGET_SUBREDDITS} for Tudor BB36 (79500)...")

    # Streams new submissions in real time
    for post in subreddit.stream.submissions(skip_existing=True, pause_after=0):
        if post is None:
            time.sleep(1)
            continue

        if is_target_deal(post):
            print(f"Match found: {post.title}")
            notify_discord(post)


if __name__ == "__main__":
    while True:
        try:
            run_agent()
        except Exception as err:
            print(f"Stream dropped ({err}), retrying in 10s...")
            time.sleep(10)
