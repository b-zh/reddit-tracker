# Reddit Watch Deal Tracker ⌚

Automated deal monitor checking `r/watchexchange`, `r/watchexchangecanada`, and `r/watch_swap` for target watch references (Tudor Black Bay 36, ref. 79500).

---

## ⚠️ Maintenance & Token Expiration

> **GitHub Personal Access Token (PAT) Expiration Notice:**
> The token used by `cron-job.org` to trigger GitHub Actions runs has a **90-day validity period**.
>
> **Token Expiration Date:** November 28 2026

### How to Renew the Token:
1. Go to **GitHub** $\rightarrow$ [Settings > Developer Settings > Personal access tokens](https://github.com/settings/tokens).
2. Generate a new token (or click **Regenerate token**) with `repo` and `workflow` permissions.
3. Open [cron-job.org](https://cron-job.org) $\rightarrow$ Edit the `Reddit Watch Tracker Trigger` job.
4. Under **Headers**, update the `Authorization` header value:
   `Bearer ghp_YOUR_NEW_TOKEN_HERE`
5. Save the job and run a **Test run** to confirm you get `204 No Content`.
