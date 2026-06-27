# mcp-bricks-co

MCP (Model Context Protocol) server for the [bricks.co](https://bricks.co) real estate crowdfunding platform. Connects Claude Code to your bricks.co account — query your portfolio, track revenues, spot payment issues, and run investment simulations directly from your AI assistant.

---

## What it does

| Capability | Description |
|---|---|
| **Portfolio analysis** | Current value, invested capital, revenues by period, property details |
| **Cash flow projection** | Upcoming reimbursements and revenues month by month |
| **Issues detection** | Parallel scan of all properties for impayés, retards, incidents |
| **Investment opportunities** | Open projects filtered by rate, contract type, maturity |
| **Wallet management** | Balances, transaction history, withdrawable amounts |

---

## Architecture

```
Claude Code
    │
    │  MCP (stdio)
    ▼
mcp-bricks server  ──►  https://api.bricks.co
    │
    │  Cookie session (persisted to disk)
    ▼
~/.local/share/bricks-co/session.json
```

The server runs as a local process on your Mac via `uv run`. It authenticates with bricks.co using a session cookie stored on disk and exposes the API as MCP tools callable from Claude Code.

> **Why not Docker?** bricks.co's API is protected by Cloudflare and blocks container IP ranges. The server must run on the host machine with a residential IP.

---

## Quick start

### 1 — Prerequisites

```bash
brew install uv
```

### 2 — Clone

```bash
git clone https://github.com/clement-igonet/mcp-bricks-co
cd mcp-bricks-co
```

### 3 — Register with Claude Code

Add to `.mcp.json` at the root of your Claude Code project:

```json
{
  "mcpServers": {
    "bricks-co": {
      "command": "/opt/homebrew/bin/uv",
      "args": [
        "run",
        "--project", "/path/to/mcp-bricks-co/mcp-bricks",
        "python", "-m", "mcp_bricks.server"
      ],
      "env": {
        "PYTHONPATH": "/path/to/mcp-bricks-co/mcp-bricks/src",
        "COOKIE_FILE": "/Users/you/.local/share/bricks-co/session.json"
      }
    }
  }
}
```

### 4 — Authenticate

Ask Claude to sign you in:

```
Sign me in to bricks.co with email user@example.com
```

Claude will call `sign_in`, then `send_otp`, then `verify_otp` with the code you receive. The session cookie is saved to disk and reused across sessions.

**Alternative:** copy the `Cookie` header from any `api.bricks.co` request in your browser DevTools and call `set_session` with it.

---

## Investment rules

Defined in [`CLAUDE.md`](CLAUDE.md) — Claude enforces these automatically:

- Never invest less than **500 €** at a time
- Wait until available balance exceeds **500 €** before any action
- Minimum accepted return: **9 %/year**

---

## Example prompts

```
How much can I invest right now?
```
```
Show me all upcoming reimbursements over the next 12 months.
```
```
Scan my portfolio for payment issues and late projects.
```
```
What are the best open projects matching my investment rules?
```
```
What monthly income can I expect from bricks.co at retirement in 19 years?
```

---

## Project structure

```
.
├── .mcp.json                  # Claude Code MCP registration
├── CLAUDE.md                  # Investment rules (enforced by Claude)
├── API.md                     # bricks.co API reference
├── SOCKTAINER.md              # Docker + Apple container setup
├── docker-compose.yml         # Container deployment
└── mcp-bricks/
    ├── Dockerfile
    ├── pyproject.toml
    └── src/mcp_bricks/
        ├── server.py          # MCP tools (25 tools across 7 categories)
        └── api_client.py      # bricks.co HTTP client
```

---

## MCP tools

25 tools across 7 categories. See [`mcp-bricks/README.md`](mcp-bricks/README.md) for the full reference.

| Category | Tools |
|---|---|
| Authentication | `sign_in`, `send_otp`, `verify_otp`, `get_session`, `set_session` |
| Account | `get_profile`, `get_account`, `get_balances` |
| Portfolio | `get_wealth_metrics`, `get_revenue`, `get_properties_summary`, `get_recent_property_updates`, `get_portfolio_properties`, `get_portfolio_property` |
| Issues | `get_issues_report` |
| Projects | `list_projects`, `list_financed_projects`, `get_recent_properties`, `get_property_investor_count`, `get_project` |
| Transactions | `list_transactions`, `get_boosted_balance_home`, `get_boosted_balance` |
| Config | `get_voting_status`, `get_news`, `get_news_banner`, `get_community_stats`, `get_feature_flags`, `get_app_config` |

---

## API reference

Full endpoint documentation in [`API.md`](API.md).

---

## Docker / Apple container

See [`SOCKTAINER.md`](SOCKTAINER.md) for running via Docker Compose or Apple's native `container` CLI on Apple Silicon.

```bash
docker compose up -d
```

> Note: the MCP server itself should still run via `uv` on the host for Cloudflare compatibility. Docker is useful for auxiliary services or CI.

---

## Dependencies

| Package | Version |
|---|---|
| `mcp[cli]` | ≥ 1.9.0 |
| `httpx` | ≥ 0.27.0 |
| Python | ≥ 3.11 |
