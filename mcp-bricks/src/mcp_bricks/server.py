import asyncio
import json
import re

from mcp.server.fastmcp import FastMCP

from mcp_bricks.api_client import BricksApiClient

mcp = FastMCP("mcp-bricks-co")
api = BricksApiClient()


def _json(data: object) -> str:
    return json.dumps(data, indent=2, ensure_ascii=False)


# ── Session injection ────────────────────────────────────────────────────────


@mcp.tool()
async def set_session(cookie_header: str) -> str:
    """Inject a session cookie copied from browser dev tools.
    Paste the full value of the Cookie request header from any api.bricks.co request.
    Example: 'better-auth.session_token=abc123xyz'
    """
    api.set_cookies_from_string(cookie_header)
    return "Session cookie saved. Try get_session to verify."


# ── Auth ─────────────────────────────────────────────────────────────────────


@mcp.tool()
async def sign_in(email: str, password: str) -> str:
    """Sign in to bricks.co with email and password. May trigger a 2FA OTP flow."""
    return _json(await api.sign_in(email, password))


@mcp.tool()
async def send_otp() -> str:
    """Send a one-time password for two-factor authentication."""
    return _json(await api.send_otp())


@mcp.tool()
async def verify_otp(code: str) -> str:
    """Verify the OTP code received by email or SMS to complete sign in."""
    return _json(await api.verify_otp(code))


@mcp.tool()
async def get_session() -> str:
    """Get details about the current authenticated session (expiry, IP, user agent)."""
    return _json(await api.get_session())


# ── Account ──────────────────────────────────────────────────────────────────


@mcp.tool()
async def get_profile() -> str:
    """Get the current user's profile including KYC status and personal info."""
    return _json(await api.get_me())


@mcp.tool()
async def get_account() -> str:
    """Get full account details including personal info, business type, and birth info."""
    return _json(await api.get_account())


@mcp.tool()
async def get_balances() -> str:
    """Get all wallet balances: available, gift, total, withdrawable, and claimable gains.
    Amounts are in centimes (divide by 100 for euros)."""
    return _json(await api.get_balances())


# ── Portfolio ─────────────────────────────────────────────────────────────────


@mcp.tool()
async def get_wealth_metrics() -> str:
    """Get portfolio wealth overview: current value, invested amount, available balance."""
    return _json(await api.get_wealth_metrics())


@mcp.tool()
async def get_revenue(start_date: str | None = None, end_date: str | None = None) -> str:
    """Get revenue analytics for a date range.

    Args:
        start_date: Start month in YYYY-MM format, e.g. '2025-01'
        end_date: End month in YYYY-MM format, e.g. '2025-12'
    """
    return _json(await api.get_revenue(start_date, end_date))


@mcp.tool()
async def get_properties_summary() -> str:
    """Get the total count of bricks owned and the number of projects invested in."""
    return _json(await api.get_properties_summary())


@mcp.tool()
async def get_recent_property_updates() -> str:
    """Get highlighted monthly updates for owned properties from the last 30 days."""
    return _json(await api.get_recent_property_updates())


# ── Boosted balance ───────────────────────────────────────────────────────────


@mcp.tool()
async def get_boosted_balance_home() -> str:
    """Get a summary of claimable gains, claimed gains, current rate, and theoretical daily gains."""
    return _json(await api.get_boosted_balance_home())


@mcp.tool()
async def get_boosted_balance() -> str:
    """Get detailed boosted balance: rate, campaign name, total wallet balance, daily gains,
    and recent transaction history."""
    return _json(await api.get_boosted_balance())


# ── Voting ────────────────────────────────────────────────────────────────────


@mcp.tool()
async def get_voting_status() -> str:
    """Check voting eligibility, pending votes count, and get a tokenized voting platform URL."""
    return _json(await api.get_voting_status())


# ── Projects & Properties ─────────────────────────────────────────────────────


@mcp.tool()
async def list_projects() -> str:
    """List all ongoing investment projects with contract types, gallery, and thumbnails."""
    return _json(await api.list_projects())


@mcp.tool()
async def list_financed_projects() -> str:
    """List financed projects grouped by month."""
    return _json(await api.list_financed_projects())


@mcp.tool()
async def get_recent_properties() -> str:
    """Get recently listed properties with funding progress and key info."""
    return _json(await api.get_recent_properties())


@mcp.tool()
async def get_property_investor_count(property_id: str) -> str:
    """Get the number of interested investors for a specific property.

    Args:
        property_id: The property UUID
    """
    return _json(await api.get_property_investor_count(property_id))


@mcp.tool()
async def get_project(project_id: str) -> str:
    """Get full details for a single project: maturity date, revenue start date,
    yearly return rate, principal repayment status, and contract type.

    Args:
        project_id: The project UUID
    """
    return _json(await api.get_project(project_id))


@mcp.tool()
async def get_portfolio_properties() -> str:
    """Get all investor portfolio properties grouped by status (ongoing / refunded).
    Includes remaining contract months, brick count, and refund status per property.
    Key for tracking upcoming capital reimbursements."""
    return _json(await api.get_portfolio_properties())


@mcp.tool()
async def get_portfolio_property(property_id: str) -> str:
    """Get detailed investor position for a specific portfolio property:
    contract duration, remaining months, past revenues, cumulated revenues,
    and full propertyUpdates history (payment delays, impayés, incidents).

    Args:
        property_id: The property UUID
    """
    return _json(await api.get_portfolio_property(property_id))


# Keywords that signal a payment problem in a property update description
_ISSUE_PATTERNS = re.compile(
    r"impay[ée]|retard|régularis|repouss[ée]|incident|manquant|défaut|non.?versé|"
    r"en.?attente.*loyer|loyer.*attente|problème|difficulté|aléa",
    re.IGNORECASE,
)


@mcp.tool()
async def get_issues_report(max_properties: int = 20) -> str:
    """Scan the full portfolio and return a structured report of problematic projects.

    Identifies issues by:
    - refundStatus == 'partial' (capital partially returned, possibly a default)
    - propertyUpdates containing keywords: impayé, retard, régularis, repoussé, incident…

    Fetches individual property history for each candidate (parallel calls, capped at
    max_properties to stay within API rate limits).

    Args:
        max_properties: Max number of individual property details to fetch (default 20).
    """
    # Step 1 — get portfolio summary
    summary = await api.get_portfolio_properties()
    ongoing: list[dict] = summary.get("ongoing", [])

    # Step 2 — first pass: flag candidates from summary fields only
    candidates: list[dict] = []
    for p in ongoing:
        flags: list[str] = []
        if p.get("refundStatus") not in (None, "none"):
            flags.append(f"refundStatus={p['refundStatus']}")
        candidates.append({
            "propertyId": p["propertyId"],
            "propertyName": p["propertyName"],
            "brickCount": p["brickCount"],
            "brickPrice": p["brickPrice"],
            "capitalEuros": p["brickCount"] * p["brickPrice"] / 100,
            "contractType": p.get("investorContractType"),
            "remainingMonths": p.get("contractRemainingMonths"),
            "lastEcheancePeriod": p.get("lastEcheancePeriod"),
            "cumulatedRevenues": p.get("cumulatedRevenues", 0) / 100,
            "summaryFlags": flags,
        })

    # Step 3 — fetch property details in parallel (capped)
    to_fetch = candidates[:max_properties]

    async def fetch_detail(prop: dict) -> dict:
        try:
            detail = await api.get_portfolio_property(prop["propertyId"])
        except Exception as exc:
            prop["fetchError"] = str(exc)
            return prop

        updates: list[dict] = detail.get("propertyUpdates", [])
        problem_updates = [
            {"date": u.get("date", "")[:10], "description": u.get("description", "")}
            for u in updates
            if _ISSUE_PATTERNS.search(u.get("description", ""))
        ]
        prop["problemUpdatesCount"] = len(problem_updates)
        prop["problemUpdates"] = sorted(
            problem_updates, key=lambda x: x["date"], reverse=True
        )
        if problem_updates and not prop["summaryFlags"]:
            prop["summaryFlags"].append("problem_updates_detected")
        return prop

    results = await asyncio.gather(*[fetch_detail(p) for p in to_fetch])

    # Step 4 — keep only truly problematic ones, sort by severity
    problematic = [
        r for r in results
        if r.get("summaryFlags") or r.get("problemUpdatesCount", 0) > 0
    ]
    problematic.sort(
        key=lambda x: (len(x.get("summaryFlags", [])) + x.get("problemUpdatesCount", 0)),
        reverse=True,
    )

    return _json({
        "scanned": len(to_fetch),
        "totalOngoing": len(ongoing),
        "problematicCount": len(problematic),
        "properties": problematic,
    })


# ── Transactions ──────────────────────────────────────────────────────────────


@mcp.tool()
async def list_transactions(cursor: int = 0, take: int = 20) -> str:
    """List wallet transactions with cursor-based pagination.
    Returns transaction kind, amount, date, and status.

    Args:
        cursor: Start offset (default 0)
        take: Page size (default 20)
    """
    return _json(await api.list_transactions(cursor, take))


# ── Content / Config ──────────────────────────────────────────────────────────


@mcp.tool()
async def get_feature_flags() -> str:
    """Get the web app feature flags (enabled features and experiments)."""
    return _json(await api.get_feature_flags())


@mcp.tool()
async def get_news() -> str:
    """Get the home page news item with image URLs and call-to-action."""
    return _json(await api.get_news())


@mcp.tool()
async def get_news_banner() -> str:
    """Get the promotional news banner content (multilingual: FR/EN)."""
    return _json(await api.get_news_banner())


@mcp.tool()
async def get_community_stats() -> str:
    """Get community fundraising stats: total amount invested and share count."""
    return _json(await api.get_community_stats())


@mcp.tool()
async def get_app_config() -> str:
    """Get the app runtime configuration."""
    return _json(await api.get_app_config())


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
