import json
import os
from pathlib import Path

import httpx

API_BASE = "https://api.bricks.co"
COOKIE_FILE = Path(os.environ.get("COOKIE_FILE", "/data/session.json"))

HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Content-Type": "application/json",
    "Cache-Control": "no-cache",
    "Origin": "https://app.bricks.co",
    "Referer": "https://app.bricks.co/",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36",
}


class BricksApiClient:
    def __init__(self) -> None:
        self._cookies: dict[str, str] = {}
        self._load_cookies()
        self._client = httpx.AsyncClient(
            base_url=API_BASE,
            headers=HEADERS,
            follow_redirects=True,
        )

    def _load_cookies(self) -> None:
        try:
            if COOKIE_FILE.exists():
                self._cookies = json.loads(COOKIE_FILE.read_text())
        except Exception:
            pass

    def _save_cookies(self) -> None:
        try:
            COOKIE_FILE.parent.mkdir(parents=True, exist_ok=True)
            COOKIE_FILE.write_text(json.dumps(self._cookies))
        except Exception:
            pass

    def _sync_cookies_from_response(self, response: httpx.Response) -> None:
        for name, value in response.cookies.items():
            self._cookies[name] = value
        self._save_cookies()

    async def _get(self, path: str, **kwargs) -> object:
        r = await self._client.get(path, cookies=self._cookies, **kwargs)
        r.raise_for_status()
        self._sync_cookies_from_response(r)
        return r.json()

    async def _post(self, path: str, body: dict) -> object:
        r = await self._client.post(path, json=body, cookies=self._cookies)
        r.raise_for_status()
        self._sync_cookies_from_response(r)
        return r.json()

    def set_cookies_from_string(self, cookie_header: str) -> None:
        """Parse a raw Cookie header string and persist it."""
        for part in cookie_header.split(";"):
            part = part.strip()
            if "=" in part:
                name, _, value = part.partition("=")
                self._cookies[name.strip()] = value.strip()
        self._save_cookies()

    # ── Auth ────────────────────────────────────────────────────────────────

    async def sign_in(self, email: str, password: str) -> object:
        return await self._post("/api/auth/sign-in/email", {"email": email, "password": password})

    async def send_otp(self) -> object:
        return await self._post("/api/auth/two-factor/send-otp", {})

    async def verify_otp(self, code: str) -> object:
        return await self._post("/api/auth/two-factor/verify-otp", {"code": code})

    async def get_session(self) -> object:
        return await self._get("/api/auth/get-session")

    # ── Account ─────────────────────────────────────────────────────────────

    async def get_me(self) -> object:
        return await self._get("/customers/me")

    async def get_account(self) -> object:
        return await self._get("/customers/account")

    async def get_balances(self) -> object:
        return await self._get("/customers/balances")

    # ── Portfolio ────────────────────────────────────────────────────────────

    async def get_wealth_metrics(self) -> object:
        return await self._get("/investor/portfolio/wealth/home-metrics")

    async def get_revenue(self, start_date: str | None = None, end_date: str | None = None) -> object:
        params: dict[str, str] = {}
        if start_date:
            params["startDate"] = start_date
        if end_date:
            params["endDate"] = end_date
        return await self._get("/investor/portfolio/revenue", params=params)

    async def get_properties_summary(self) -> object:
        return await self._get("/investor/portfolio/properties/my-projects-and-bricks-count")

    async def get_recent_property_updates(self) -> object:
        return await self._get(
            "/investor/portfolio/properties/my-properties-last-30-days-highlighted-monthly-updates"
        )

    # ── Boosted balance ──────────────────────────────────────────────────────

    async def get_boosted_balance_home(self) -> object:
        return await self._get("/investor/boosted-balance/home-view")

    async def get_boosted_balance(self) -> object:
        return await self._get("/investor/boosted-balance/view")

    # ── Voting ───────────────────────────────────────────────────────────────

    async def get_voting_status(self) -> object:
        has_votes = await self._get("/investor/voting/has-votes")
        pending = await self._get("/investor/voting/pending-votes-count")
        platform = await self._get("/investor/voting/platform-url")
        return {"hasVotes": has_votes, "pendingVotesCount": pending, "platformUrl": platform}

    # ── Projects & Properties ────────────────────────────────────────────────

    async def list_projects(self) -> object:
        return await self._get("/projects")

    async def list_financed_projects(self) -> object:
        return await self._get("/projects/financed")

    async def get_recent_properties(self) -> object:
        return await self._get("/properties/preview-recent-properties")

    async def get_property_investor_count(self, property_id: str) -> object:
        return await self._get(f"/properties/{property_id}/interested-investors-count")

    async def get_project(self, project_id: str) -> object:
        return await self._get(f"/projects/{project_id}")

    async def get_portfolio_properties(self) -> object:
        return await self._get("/investor/portfolio/properties")

    async def get_portfolio_property(self, property_id: str) -> object:
        return await self._get(f"/investor/portfolio/properties/{property_id}")

    # ── Transactions ─────────────────────────────────────────────────────────

    async def list_transactions(self, cursor: int = 0, take: int = 20) -> object:
        return await self._get("/wallet-transactions", params={"cursor": cursor, "take": take})

    # ── Content / Config ─────────────────────────────────────────────────────

    async def get_feature_flags(self) -> object:
        return await self._get("/feature-flag/web")

    async def get_news(self) -> object:
        return await self._get("/home/news")

    async def get_news_banner(self) -> object:
        return await self._get("/news-banner")

    async def get_community_stats(self) -> object:
        return await self._get("/investor/community-fundraising")

    async def get_app_config(self) -> object:
        return await self._get("/app-config")
