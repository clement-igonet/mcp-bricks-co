# mcp-bricks-co

MCP server for the [bricks.co](https://bricks.co) real estate crowdfunding platform.  
Exposes the bricks.co private API as [MCP tools](https://modelcontextprotocol.io/) for use with Claude Code or any MCP-compatible client.

---

## Tools reference

### Authentication

| Tool | Description |
|---|---|
| `sign_in(email, password)` | Sign in with email and password. May trigger a 2FA OTP flow. |
| `send_otp()` | Send a one-time password for two-factor authentication. |
| `verify_otp(code)` | Verify the OTP code received by email or SMS to complete sign-in. |
| `get_session()` | Get details about the current authenticated session (expiry, IP, user agent). |
| `set_session(cookie_header)` | Inject a session cookie copied from browser DevTools. Paste the full `Cookie` request header from any `api.bricks.co` request. |

### Account

| Tool | Description |
|---|---|
| `get_profile()` | Get the current user's profile including KYC status and personal info. |
| `get_account()` | Get full account details: personal info, business type, birth info. |
| `get_balances()` | Get all wallet balances: available, gift, total, withdrawable, claimable gains. Amounts in centimes (÷100 for euros). |

### Portfolio

| Tool | Description |
|---|---|
| `get_wealth_metrics()` | Portfolio overview: current value, invested amount, available balance. |
| `get_revenue(start_date, end_date)` | Revenue analytics for a date range. Dates in `YYYY-MM` format (e.g. `2025-01`). |
| `get_properties_summary()` | Total count of bricks owned and number of projects invested in. |
| `get_recent_property_updates()` | Highlighted monthly updates for owned properties from the last 30 days. |
| `get_portfolio_properties()` | All portfolio properties grouped by status (ongoing / refunded). Includes remaining contract months, brick count, and refund status. Key for tracking upcoming capital reimbursements. |
| `get_portfolio_property(property_id)` | Detailed investor position for a specific property: contract duration, remaining months, past revenues, cumulated revenues, and full `propertyUpdates` history (payment delays, impayés, incidents). |

### Issues report

| Tool | Description |
|---|---|
| `get_issues_report(max_properties)` | Scan the full portfolio and return a structured report of problematic projects. Identifies issues by: `refundStatus == 'partial'` (partial capital return, possible default) and `propertyUpdates` containing keywords: *impayé, retard, régularis, repoussé, incident, manquant, défaut…* Fetches individual property history in parallel (capped at `max_properties`, default 20). |

### Projects & properties

| Tool | Description |
|---|---|
| `list_projects()` | List all ongoing investment projects with contract types, gallery, and thumbnails. |
| `list_financed_projects()` | List financed projects grouped by month. |
| `get_recent_properties()` | Recently listed properties with funding progress and key info. |
| `get_property_investor_count(property_id)` | Number of interested investors for a specific property. |
| `get_project(project_id)` | Full details for a single project: maturity date, revenue start date, yearly return rate, principal repayment status, contract type. |

### Wallet & transactions

| Tool | Description |
|---|---|
| `list_transactions(cursor, take)` | Wallet transactions with cursor-based pagination. Returns kind, amount, date, status. Default page size: 20. |
| `get_boosted_balance_home()` | Summary of claimable gains, claimed gains, current rate, theoretical daily gains. |
| `get_boosted_balance()` | Detailed boosted balance: rate, campaign name, total wallet balance, daily gains, recent transaction history. |

### Community & config

| Tool | Description |
|---|---|
| `get_voting_status()` | Voting eligibility, pending votes count, and tokenized voting platform URL. |
| `get_news()` | Home page news item with image URLs and call-to-action. |
| `get_news_banner()` | Promotional news banner content (multilingual FR/EN). |
| `get_community_stats()` | Community fundraising stats: total amount invested and share count. |
| `get_feature_flags()` | Web app feature flags (enabled features and experiments). |
| `get_app_config()` | App runtime configuration. |

---

## Setup

### Requirements

- Python 3.11+
- [uv](https://docs.astral.sh/uv/)

### Install

```bash
git clone https://github.com/clement-igonet/mcp-bricks-co
cd mcp-bricks-co
uv sync
```

### Session authentication

The server stores the session cookie in a JSON file (default: `/data/session.json`).  
Override with the `COOKIE_FILE` environment variable.

Two ways to authenticate:

**Option A — MCP tool (recommended)**  
Use `sign_in` then `verify_otp` from your MCP client.

**Option B — Copy from browser**  
Open DevTools on `app.bricks.co`, copy the `Cookie` header from any `api.bricks.co` request, then call:
```
set_session("better-auth.session_token=abc123...")
```

---

## Register with Claude Code

Add to `.mcp.json` at the root of your project:

```json
{
  "mcpServers": {
    "bricks-co": {
      "command": "/opt/homebrew/bin/uv",
      "args": [
        "run",
        "--project", "/path/to/mcp-bricks-co",
        "python", "-m", "mcp_bricks.server"
      ],
      "env": {
        "PYTHONPATH": "/path/to/mcp-bricks-co/src",
        "COOKIE_FILE": "/Users/you/.local/share/bricks-co/session.json"
      }
    }
  }
}
```

> **Note:** Run via `uv` on the host machine (not inside Docker). bricks.co API is protected by Cloudflare and blocks requests from container IP ranges.

---

## Run with Docker / Apple container

```bash
# Build
docker compose build
# or
container build -t mcp-bricks-co:latest .

# Run
docker compose up -d
```

See [SOCKATINER.md](../SOCKATINER.md) for Apple container + Docker Compose setup.

---

## Contract types

| Type | Return | Capital | Horizon |
|---|---|---|---|
| **Obligation** | 9 %/year fixed coupon | Guaranteed at maturity | 12–24 months |
| **Royalty** | Variable (real rents distributed) | Market price at sale | ~10 years |
| **Loan** | 9 %/year fixed | Guaranteed at maturity | Short term |

---

## Investment rules (CLAUDE.md)

- Never invest less than **500 €** at a time
- Wait until available balance exceeds **500 €** before any action
- Minimum accepted return: **9 %/year** — ignore projects below this threshold
