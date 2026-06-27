# bricks.co API

> Reverse-engineered from HAR captures and MCP server implementation.  
> Base URL: `https://api.bricks.co`  
> All responses are JSON. Monetary amounts are in **centimes** (divide by 100 for euros).

---

## Authentication

bricks.co uses cookie-based sessions (`better-auth.session_token`).

### Sign in

```
POST /api/auth/sign-in/email
```

**Body**
```json
{ "email": "user@example.com", "password": "secret" }
```

**Response** — may trigger a 2FA flow; check for `twoFactorRequired` in the response.

---

### Send OTP (2FA)

```
POST /api/auth/two-factor/send-otp
```

No body. Sends a one-time code to the registered email or phone.

---

### Verify OTP (2FA)

```
POST /api/auth/two-factor/verify-otp
```

**Body**
```json
{ "code": "123456" }
```

On success, the session cookie (`better-auth.session_token`) is set.

---

### Get session

```
GET /api/auth/get-session
```

Returns current session details: expiry, IP address, user agent.

---

## Account

### Profile

```
GET /customers/me
```

Returns KYC status, personal info, investor type.

---

### Full account

```
GET /customers/account
```

Returns personal info, business type, birth date.

---

### Wallet balances

```
GET /customers/balances
```

**Response fields** (amounts in centimes)

| Field | Description |
|---|---|
| `available` | Withdrawable balance |
| `gift` | Bonus/gift credit |
| `total` | Total wallet balance |
| `withdrawable` | Amount that can be transferred to bank |
| `hasClaimableGains` | Boolean — boosted gains available |

---

## Portfolio

### Wealth overview

```
GET /investor/portfolio/wealth/home-metrics
```

Returns current portfolio value, invested amount, available balance.

---

### Revenue analytics

```
GET /investor/portfolio/revenue?startDate=YYYY-MM&endDate=YYYY-MM
```

**Query params**

| Param | Format | Description |
|---|---|---|
| `startDate` | `YYYY-MM` | Start month (e.g. `2025-01`) |
| `endDate` | `YYYY-MM` | End month (e.g. `2025-12`) |

Returns monthly revenue breakdown by contract type (royalty / obligation).

---

### Properties summary

```
GET /investor/portfolio/properties/my-projects-and-bricks-count
```

Returns total number of bricks owned and number of active projects.

---

### Recent property updates (last 30 days)

```
GET /investor/portfolio/properties/my-properties-last-30-days-highlighted-monthly-updates
```

Returns highlighted events (payment received, delay, regularization) for the last 30 days.

---

### All portfolio properties

```
GET /investor/portfolio/properties
```

Returns two arrays: `ongoing` and `refunded`.

**Key fields per property**

| Field | Description |
|---|---|
| `propertyId` | UUID |
| `propertyName` | Display name |
| `brickCount` | Number of bricks held |
| `brickPrice` | Price per brick in centimes |
| `investorContractType` | `obligation` \| `royalty` \| `loan` |
| `contractRemainingMonths` | Months until maturity |
| `lastEcheancePeriod` | Last scheduled payment period |
| `cumulatedRevenues` | Total revenues received, in centimes |
| `refundStatus` | `none` \| `partial` \| `full` |

---

### Single portfolio property

```
GET /investor/portfolio/properties/{property_id}
```

Full investor position for a property. Includes:

- Contract details (duration, start date, maturity date, yearly rate)
- Cumulated revenues
- `propertyUpdates` — full history of updates (payment confirmations, delays, incidents)

**`propertyUpdates` item fields**

| Field | Description |
|---|---|
| `date` | ISO 8601 date |
| `description` | Free-text update (French) — scan for *impayé, retard, régularis…* |
| `type` | Update category |

---

## Boosted balance

### Home view

```
GET /investor/boosted-balance/home-view
```

Returns claimable gains, claimed gains, current rate, theoretical daily gains.

---

### Detail view

```
GET /investor/boosted-balance/view
```

Returns rate, campaign name, total wallet balance, daily gains, recent transaction history.

---

## Voting

```
GET /investor/voting/has-votes
GET /investor/voting/pending-votes-count
GET /investor/voting/platform-url
```

Returns voting eligibility status, number of pending votes, and a tokenized URL to the voting platform.

---

## Projects

### List open projects

```
GET /projects
```

Returns all projects currently open for investment: contract type, thumbnail, funding progress.

---

### Financed projects

```
GET /projects/financed
```

Returns financed projects grouped by month.

---

### Single project

```
GET /projects/{project_id}
```

**Key fields**

| Field | Description |
|---|---|
| `yearlyReturnRate` | Advertised annual return (e.g. `0.09` = 9 %) |
| `contractType` | `obligation` \| `royalty` \| `loan` |
| `maturityDate` | Capital repayment date (obligations) |
| `revenueStartDate` | Date from which interest accrues |
| `principalRepaymentStatus` | Repayment state |
| `brickPrice` | Price per brick in centimes |
| `totalBricks` | Total bricks in the project |
| `availableBricks` | Bricks still available |

---

## Properties (marketplace)

### Recent listings

```
GET /properties/preview-recent-properties
```

Returns recently listed properties with funding progress.

---

### Interested investor count

```
GET /properties/{property_id}/interested-investors-count
```

Returns the number of investors who have shown interest in a property.

---

## Wallet transactions

```
GET /wallet-transactions?cursor=0&take=20
```

**Query params**

| Param | Default | Description |
|---|---|---|
| `cursor` | `0` | Pagination offset |
| `take` | `20` | Page size |

**Transaction kinds**

| Kind | Description |
|---|---|
| `primary_purchase` | Investment in a project |
| `primary_purchase_with_refund` | Investment funded by a capital refund |
| `recurring_revenue` | Monthly interest or rent payment |
| `obligation_principal_repayment_full` | Full capital returned at maturity |
| `obligation_principal_repayment_partial` | Partial capital return |
| `deposit` | Bank transfer in |
| `withdrawal` | Bank transfer out |

**Key fields per transaction**

| Field | Description |
|---|---|
| `value` | Amount in centimes (signed — negative = debit) |
| `kind` | Transaction kind (see above) |
| `date` | ISO 8601 timestamp |
| `status` | `completed` \| `pending` \| `failed` |

---

## Community & config

### Community stats

```
GET /investor/community-fundraising
```

Returns total amount raised by the community and total number of shares.

---

### Feature flags

```
GET /feature-flag/web
```

Returns enabled features and A/B experiments for the web app.

---

### News

```
GET /home/news
```

Returns the home page news item with image URLs and call-to-action.

---

### News banner

```
GET /news-banner
```

Returns the promotional banner content in French and English.

---

### App config

```
GET /app-config
```

Returns app runtime configuration (API versions, feature toggles, limits).

---

## Notes

### Contract types

| Type | Return | Capital guarantee | Horizon |
|---|---|---|---|
| `obligation` | 9 %/year fixed coupon | ✅ Yes — at maturity | 12–24 months |
| `royalty` | Variable (real rents) | ❌ No — market price at sale | ~10 years |
| `loan` | 9 %/year fixed coupon | ✅ Yes — at maturity | Short term |

### Amount encoding

All monetary values are integers in **centimes**. Divide by 100 to get euros.

```python
euros = response["value"] / 100
```

### Pagination

`/wallet-transactions` uses cursor-based pagination:

```
GET /wallet-transactions?cursor=0&take=20   # page 1
GET /wallet-transactions?cursor=20&take=20  # page 2
```

### Cloudflare protection

`api.bricks.co` is behind Cloudflare and blocks requests from cloud/VPN IP ranges. The session cookie must be obtained from a residential IP. Run the MCP server on the host machine (not inside Docker) to avoid IP blocking.
