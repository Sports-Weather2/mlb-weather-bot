Looking at your file I can see it has some formatting issues — the `[2.0.8]` entry is completely missing and there are some broken sections around `[2.0.9]` and `[2.0.5]`. Here's the complete corrected file:

```markdown
# Changelog

All notable changes to the MLB Weather Monitoring System.

The format is based on [Keep a Changelog](https://keepachangelog.com/).

---

## [2.0.11] - 2026-05-02

### 🐛 Fixed

#### `weather-update-v2.yml` — Duplicate Daily Report Posting
- **Root cause:** `last_weather_run.txt` was committed in the same
  git step as `analytics.json` and `ANALYTICS.md` — when the
  `mlb-status-monitor-v2.yml` ran simultaneously it caused a
  **merge conflict on analytics files** during `git pull --rebase`
  — the rebase failed, leaving the repo in detached HEAD state,
  and the push failed silently
- **Symptom:** May 2, 2026 — daily report posted **twice**:
  - Run #74 at 7:10 AM PT — posted correctly ✅
  - Run #75 at 7:55 AM PT — posted duplicate ❌
  - Both were Scheduled cron triggers (6 AM + 7 AM backup)
  - Run #74 commit logs showed:
    `CONFLICT (content): Merge conflict in ANALYTICS.md`
    `CONFLICT (content): Merge conflict in analytics.json`
    `⚠️ WARNING: Push failed — dedup file may not persist`
  - Run #75 saw old date in `last_weather_run.txt` because
    #74's push failed — thought it was first run and posted again
- **Fix 1 — Separate dedup commit:** `last_weather_run.txt` now
  commits in its **own dedicated step** ("Mark as ran today")
  immediately after the weather bot runs — before analytics files
  are touched. This simple commit has no conflict risk since no
  other workflow writes to `last_weather_run.txt`
- **Fix 2 — Rebase abort fallback:** Added `|| git rebase --abort
  || true` after `git pull --rebase` so the repo never gets stuck
  in detached HEAD state on conflict
- **Fix 3 — Force-with-lease push:** Changed `git push` fallback
  from silent warning to `git push --force-with-lease` which
  handles cases where the remote has moved ahead

### 🎯 Impact

- **Duplicate daily reports eliminated** — `last_weather_run.txt`
  now persists correctly even when analytics files conflict
- **Zero impact on analytics** — `analytics.json`, `ANALYTICS.md`
  and `STATUS.md` still committed in the same step as before
- **Zero impact on alert accuracy** — weather data, thresholds
  and Slack formatting all unchanged

### 📊 Before vs After

| | Before Fix | After Fix |
|---|---|---|
| `last_weather_run.txt` commit | Same step as analytics | ✅ Own dedicated step |
| Analytics conflict impact | Blocks dedup file save | ✅ Dedup already saved |
| Push failure handling | Silent warning only | ✅ Rebase abort + force-with-lease |
| Duplicate alert risk | High when conflicts occur | ✅ Eliminated |

### 📋 Files Changed

| File | Type | Summary |
|---|---|---|
| `weather-update-v2.yml` | 🔧 Modified | Separate dedup commit + rebase abort + force-with-lease |

---

## [2.0.10] - 2026-04-30

### 🐛 Fixed

#### `high-risk-alert-v2.yml` — `config.json` Not Committed After 10 AM Run
- **Root cause:** Same issue as `weather-update-v2.yml` (fixed in
  v2.0.9) — the commit step in `high-risk-alert-v2.yml` was also
  missing `git add config.json || true`
- **Impact:** The 10 AM high risk alert runs `update_schedule.py`
  before checking weather — but the fresh `config.json` was never
  committed back to the repo from this workflow either
- **Fix:** Added `git add config.json || true` to the "Commit
  tracking, analytics, and keep-alive" step — now both the 7 AM
  and 10 AM workflows commit the fresh schedule

### 🔧 Changed

#### `update_schedule.py` — Defensive Venue Mappings Added
- Added proactive safety mappings for known and potential venue
  renames/alternate names to prevent future missing game issues
- **`Daikin Park` → `Houston,US`** ✅ NEW
  - Astros' Minute Maid Park may have been renamed — added
    proactively before a home Astros game confirms it in the
    MLB API response
- **`LoanDepot Park` → `Miami,US`** ✅ NEW
  - Alternate capitalization of `loanDepot park`
- **`loanDepot Park` → `Miami,US`** ✅ NEW
  - Alternate capitalization of `loanDepot park`
- **`Loan Depot Park` → `Miami,US`** ✅ NEW
  - Alternate spacing variant of `loanDepot park`

### 🎯 Impact

- **`config.json` now committed by both workflows** — 7 AM and
  10 AM runs both persist the fresh schedule to the repo
- **Zero unknown venue warnings** confirmed in April 29 run logs
  — all 15 venues mapped correctly with no defaults to Phoenix
- **Defensive mappings prevent future silent exclusions**

### 📊 Venue Audit — April 29, 2026

| Venue | Location | Status |
|---|---|---|
| Progressive Field | Cleveland,US | ✅ |
| Rate Field | Chicago,US | ✅ Fixed v2.0.9 |
| Target Field | Minneapolis,US | ✅ |
| Globe Life Field | Arlington,US | ✅ |
| Rogers Centre | Toronto,CA | ✅ Excluded dome |
| UNIQLO Field at Dodger Stadium | Los Angeles,US | ✅ Fixed v2.0.9 |
| Petco Park | San Diego,US | ✅ |
| Oriole Park at Camden Yards | Baltimore,US | ✅ |
| Great American Ball Park | Cincinnati,US | ✅ |
| PNC Park | Pittsburgh,US | ✅ |
| Citizens Bank Park | Philadelphia,US | ✅ |
| Citi Field | New York,US | ✅ |
| Truist Park | Atlanta,US | ✅ |
| American Family Field | Milwaukee,US | ✅ |
| Sutter Health Park | Oakland,US | ✅ |

### 📋 Files Changed

| File | Type | Summary |
|---|---|---|
| `high-risk-alert-v2.yml` | 🔧 Modified | Added `git add config.json \|\| true` to commit step |
| `update_schedule.py` | 🔧 Modified | Added 4 defensive venue name mappings |

---

## [2.0.9] - 2026-04-29

### 🐛 Fixed

#### `weather-update-v2.yml` — `config.json` Never Committed to Repo
- **Root cause:** The commit step in `weather-update-v2.yml` was
  missing `git add config.json || true` — `update_schedule.py`
  wrote fresh schedule data to `config.json` on the GitHub Actions
  VM every morning but it was never committed back to the repo
- **Symptom:** `config.json` was permanently stuck on
  **March 6, 2026 Spring Training data** — every daily report
  and high risk alert was running against 6-week-old game data
  meaning many Regular Season games were completely missing
  from weather monitoring
- **Real-world impact:** April 29 daily report missed:
  - Angels vs White Sox (Rate Field)
  - Marlins vs Dodgers (UNIQLO Field at Dodger Stadium)
  - And potentially many other games since Regular Season started
- **Fix:** Added `git add config.json || true` to the
  "Commit run tracking, analytics, and keep-alive" step in
  `weather-update-v2.yml`

#### `update_schedule.py` — Two Missing Venue Mappings
- **`Rate Field` → `Chicago,US`** ✅ NEW
  - White Sox renamed their stadium from Guaranteed Rate Field
    to Rate Field — MLB API now returns `"Rate Field"` which
    was not in the venue mapping, causing it to fall through
    to the `Phoenix,US` default → incorrectly mapped to
    Chase Field (retractable roof) → excluded from weather
    monitoring entirely
- **`UNIQLO Field at Dodger Stadium` → `Los Angeles,US`** ✅ NEW
  - Dodger Stadium was renamed with a sponsorship prefix —
    MLB API now returns `"UNIQLO Field at Dodger Stadium"`
    which was not mapped, also falling to `Phoenix,US` default

#### `last_weather_run.txt` — Manual Reset Required Today
- File was cleared manually on April 29 to force a fresh run
  after discovering the stale `config.json` issue
- Going forward this should not be needed

### 🔧 Changed

#### `weather-update-v2.yml` — Added `config.json` to Commit Step
- Added `git add config.json || true` to commit step

### 🎯 Impact

- **`config.json` now updates daily** — always reflects today's
  actual MLB schedule, never stale
- **All games now correctly monitored** — no more missing games
  due to venue mapping failures
- **Root cause of missing games resolved**

### 📊 Venue Mapping — Full Fix Summary

| Venue | Old Mapping | New Mapping | Impact |
|---|---|---|---|
| `Rate Field` | ❌ Phoenix,US (Chase Field roof) | ✅ Chicago,US | White Sox now monitored |
| `UNIQLO Field at Dodger Stadium` | ❌ Phoenix,US (Chase Field roof) | ✅ Los Angeles,US | Dodgers now monitored |

### 📋 Files Changed

| File | Type | Summary |
|---|---|---|
| `weather-update-v2.yml` | 🔧 Modified | Added `git add config.json \|\| true` to commit step |
| `update_schedule.py` | 🔧 Modified | Added `Rate Field` + `UNIQLO Field at Dodger Stadium` mappings |

---

## [2.0.8] - 2026-04-29

### 🔧 Changed

#### `weather_bot.py` — MONITOR Rain Threshold Lowered: 45% → 35%
- **Root cause:** MONITOR threshold of 45% was missing games that
  PropFinder (propfinder.app/weather) flagged as 🟡 Yellow
  (Chance For Delay) in the 30-44% rain probability range
- **Evidence:** April 29, 2026 cross-check against PropFinder
  showed two gaps:
  - PNC Park — 30% rain → PropFinder 🟡 Yellow → Bot 🟢 CLEAR ❌
  - Rate Field — 18% rain → PropFinder 🟡 Yellow → Bot 🟢 CLEAR
- **Fix:** Lowered `monitor` section `rain_prob` from 45 → 35
  in `IMPACT_RULES` in `weather_bot.py`
- **Only affects `#gameday-weather`** — MONITOR tier only appears
  in the 7 AM daily report. `#high-risk-weather-alert` and HIGH
  RISK threshold (≥80%) are completely unchanged
- `high_risk_alert.py` not affected — that file has no `monitor`
  section

### 🎯 Impact

- **30-44% rain games now show as 🟡 MONITOR** instead of 🟢 CLEAR
  — better alignment with PropFinder Yellow tier
- **No change to HIGH RISK alerts** — threshold remains ≥80%
- **No change to `#high-risk-weather-alert`** — unaffected

### 📊 Updated MONITOR Thresholds

| Condition | Old | New |
|---|---|---|
| Rain probability | ≥45% | ≥35% |
| Wind sustained | ≥20 mph | ≥20 mph (unchanged) |
| Temperature | 40–95°F | 40–95°F (unchanged) |

### 📊 PropFinder Alignment (After Fix)

| Rain % | PropFinder | Old Bot | New Bot |
|---|---|---|---|
| 30% | 🟡 Yellow | 🟢 CLEAR ❌ | 🟡 MONITOR ✅ |
| 35% | 🟡 Yellow | 🟢 CLEAR ❌ | 🟡 MONITOR ✅ |
| 40% | 🟡 Yellow | 🟢 CLEAR ❌ | 🟡 MONITOR ✅ |
| 45% | 🟡 Yellow | 🟡 MONITOR ✅ | 🟡 MONITOR ✅ |
| 59% | 🟠 Orange | 🟡 MONITOR ✅ | 🟡 MONITOR ✅ |
| 80% | 🔴 Red | 🔴 HIGH RISK ✅ | 🔴 HIGH RISK ✅ |

### 📋 Files Changed

| File | Type | Summary |
|---|---|---|
| `weather_bot.py` | 🔧 Modified | `monitor rain_prob` 45 → 35 |

---

## [2.0.7] - 2026-04-25

### 🐛 Fixed

#### `weather_bot.py` + `high_risk_alert.py` — "Chance Showers And Thunderstorms" Still Triggering HIGH RISK
- **Root cause:** The `is_slight_chance` exclusion list checked for
  `"chance thunderstorm"` as an exact substring — but NWS forecast
  text `"Chance Showers And Thunderstorms"` contains the word
  "Showers And" between "Chance" and "Thunderstorms", so it did
  not match the exclusion string and slipped through as a real
  thunderstorm threat
- **Symptom:** April 25, 2026 alert flagged Phillies vs Braves
  at Truist Park as HIGH RISK with only **49% rain probability**
  because NWS returned `"Chance Showers And Thunderstorms"` —
  cross-checked against PropFinder (propfinder.app/weather)
  which showed the same game as 🟡 Yellow (Chance For Delay),
  not red HIGH RISK
- **Cross-check result:** 13 of 14 games correct (93% accuracy)
  before this fix — this was the one remaining false positive
- **Fix:** Added two new strings to `is_slight_chance` exclusion
  list in `get_weather_forecast()` in both files:
  - `'chance showers and thunderstorm'`
  - `'chance shower'`

### 🔧 Changed

#### Thunderstorm Exclusion List — Both Files

Full updated `is_slight_chance` list (8 items, was 6):

- `'slight chance'` — Slight Chance Thunderstorms
- `'isolated'` — Isolated Thunderstorms
- `'chance thunderstorm'` — Chance Thunderstorms
- `'chance of thunderstorm'` — Chance Of Thunderstorms
- `'few thunderstorm'` — Few Thunderstorms
- `'scattered thunderstorm'` — Scattered Thunderstorms *(added v2.0.4)*
- `'chance showers and thunderstorm'` — ✅ NEW
- `'chance shower'` — ✅ NEW

#### `analytics.json` — Accuracy Counters Reset to Clean Baseline
- All accuracy counters reset to 0
- `high_risk_predictions.json` and `false_positive_logged.json`
  also cleared to `{}`

### 🎯 Impact

- **"Chance Showers And Thunderstorms" no longer triggers HIGH RISK**
- **All known thunderstorm false positive patterns now excluded**
- **Accuracy baseline reset** — clean data collection starts today

### 📊 NWS Forecast Text — Full Exclusion Coverage (After Fix)

| NWS Forecast Text | Rain % | Result |
|---|---|---|
| Chance Showers And Thunderstorms | 49% | 🟢 CLEAR ✅ |
| Chance Thunderstorms | 35% | 🟢 CLEAR ✅ |
| Slight Chance Thunderstorms | 19% | 🟢 CLEAR ✅ |
| Scattered Thunderstorms | 45% | 🟢 CLEAR ✅ |
| Isolated Thunderstorms | 30% | 🟢 CLEAR ✅ |
| Showers And Thunderstorms | 80% | 🔴 HIGH RISK ✅ |
| Thunderstorms | 85% | 🔴 HIGH RISK ✅ |
| Heavy Rain | 88% | 🔴 HIGH RISK ✅ |

### 📋 Files Changed

| File | Type | Summary |
|---|---|---|
| `weather_bot.py` | 🔧 Modified | Added 2 strings to `is_slight_chance` exclusion list |
| `high_risk_alert.py` | 🔧 Modified | Same fix — identical change |
| `analytics.json` | 🔧 Modified | Accuracy counters reset to 0 — clean baseline |

---

## [2.0.6] - 2026-04-23

### 🔧 Changed

#### `weather_bot.py` — MONITOR Wind Threshold Raised: 15 mph → 20 mph
- **Root cause:** `wind_sustained` threshold of 15 mph was too
  sensitive — triggering MONITOR alerts on clear sunny days with
  0-12% rain probability
- **Symptom:** April 23, 2026 daily report showed 2 games as
  🟡 MONITOR with perfectly clear conditions:
  - Phillies vs Cubs — 0% rain, 78°F, 15 mph wind → MONITOR ❌
  - Padres vs Rockies — 12% rain, 63°F, 17 mph wind → MONITOR ❌
- **Fix:** Raised `wind_sustained` from 15 → 20 mph

### 🎯 Impact

- **Fewer false MONITOR alerts** on clear days with light wind
- **MONITOR now reserved for genuinely concerning conditions**

### 📊 Updated MONITOR Thresholds

| Condition | Old Threshold | New Threshold |
|---|---|---|
| Wind sustained | ≥15 mph | ≥20 mph |
| Rain probability | ≥45% | ≥45% (unchanged) |
| Temperature | 40–95°F | 40–95°F (unchanged) |

### 📋 Files Changed

| File | Type | Summary |
|---|---|---|
| `weather_bot.py` | 🔧 Modified | `wind_sustained` raised 15 → 20 mph in MONITOR thresholds |

---

## [2.0.5] - 2026-04-23

### 🔧 Changed

#### `weather_bot.py` + `high_risk_alert.py` — Priority 1: Tightened Thresholds
- **Rain threshold raised: 75% → 80%**
- **Added `'scattered thunderstorm'` to slight chance list**

#### `weather_bot.py` + `high_risk_alert.py` — Priority 2: "Why Triggered" Reason Line
- Every HIGH RISK alert now includes a `📋 Why:` line
- Examples:
  - `📋 Why: Rain 81% ≥ 80% threshold`
  - `📋 Why: Active thunderstorms + Rain 45%`
  - `📋 Why: Wind 32 mph ≥ 30 mph threshold`

#### `weather_bot.py` + `high_risk_alert.py` — Priority 4: Delay Probability Language
- Every HIGH RISK alert now includes a `🎯 Delay Probability:` line
- Four tiers:
  - `🔴 VERY HIGH — Delay or postponement likely`
  - `🟠 HIGH — Delay probable at game time`
  - `🟡 ELEVATED — Conditions may impact play`
  - `🟡 ELEVATED — Extreme cold may impact play`

#### `high_risk_alert.py` — Slack Footer Updated
- Footer updated to reflect new 80% threshold

### 🎯 Impact

- **Fewer false HIGH RISK alerts** — 80% threshold
- **Full transparency on every alert** — Why-triggered line
- **Delay severity context** — ops team knows delay probability
- **Real-time delay alerts unaffected**

### 📊 Threshold Changes

| Condition | Old Threshold | New Threshold |
|---|---|---|
| Rain HIGH RISK | ≥75% | ≥80% |
| Scattered Thunderstorms | Triggered HIGH RISK | ✅ Now ignored |
| Thunderstorms + Rain | ≥40% rain required | ≥40% rain required (unchanged) |

### 📋 Files Changed

| File | Type | Summary |
|---|---|---|
| `weather_bot.py` | 🔧 Modified | P1 thresholds, P2 why-triggered, P4 delay probability |
| `high_risk_alert.py` | 🔧 Modified | P1 thresholds, P2 why-triggered, P4 delay probability, footer |

---

## [2.0.4] - 2026-04-23

### 🐛 Fixed

#### `weather_bot.py` + `high_risk_alert.py` — False HIGH RISK Alerts from "Slight Chance Thunderstorms"
- **Root cause:** Thunderstorm detection used a broad keyword match
- **Symptom:** Atlanta Braves vs Washington Nationals flagged as
  HIGH RISK on April 22, 2026 with only **19% rain probability**
- **Real-world impact:** Team manually extended Yankees vs Red Sox
  EPG listings — system missed actual high-risk game
- **Fix — Two conditions now required:**
  1. Forecast must NOT contain a low-probability qualifier
  2. Rain probability must be **≥40%**

### 🔧 Changed

#### Thunderstorm Detection Logic — Both Files
- Old: any "thunder/tstm/lightning/storm" → HIGH RISK
- New: requires no slight-chance qualifier AND rain ≥40%

### 🎯 Impact

- **"Slight Chance Thunderstorms" no longer triggers HIGH RISK**
- **Thunderstorm alert now requires actual weather threat**

### 📊 Thunderstorm Alert Behavior (After Fix)

| NWS Forecast | Rain % | Old Result | New Result |
|---|---|---|---|
| Slight Chance Showers And Thunderstorms | 19% | 🔴 HIGH RISK ❌ | 🟢 CLEAR ✅ |
| Chance Thunderstorms | 45% | 🔴 HIGH RISK ❌ | 🔴 HIGH RISK ✅ |
| Showers And Thunderstorms | 75% | 🔴 HIGH RISK ✅ | 🔴 HIGH RISK ✅ |
| Thunderstorms | 80% | 🔴 HIGH RISK ✅ | 🔴 HIGH RISK ✅ |

### 📋 Files Changed

| File | Type | Summary |
|---|---|---|
| `weather_bot.py` | 🔧 Modified | Smarter thunderstorm detection |
| `high_risk_alert.py` | 🔧 Modified | Same thunderstorm fix + Slack footer updated |

---

## [2.0.3] - 2026-04-23

### 🐛 Fixed

#### `mlb_game_status_monitor.py` — False Positive Counter Inflating Every 10 Minutes
- **Root cause:** `check_and_log_false_positives()` called at
  end of every 10-minute monitoring cycle
- **Symptom:** `false_positives` counter reached **406** in
  `analytics.json` after only 2 days
- **Fix:** Rewrote to only log once per game when `STATE_FINAL`
- **New file `false_positive_logged.json`** prevents double counting

#### `mlb-status-monitor-v2.yml` — Two Fixes
- **Fix 1:** `SLACK_WEBHOOK` → `HIGH_RISK_WEBHOOK_URL`
- **Fix 2:** Added `git add false_positive_logged.json || true`

#### `analytics.json` — False Positive Counter Reset
- `false_positives` reset from `406` → `0`

### 🎯 Impact

- **False positive counter now accurate**
- **Real-time delay alerts now posting correctly**

### 📊 Accuracy Dashboard (After Fix)

| Metric | Before | After |
|---|---|---|
| False Positives | 406 ❌ | 0 ✅ Reset |
| Accuracy Rate | 0.0% | 100% ✅ |

### 📋 Files Changed

| File | Type | Summary |
|---|---|---|
| `mlb_game_status_monitor.py` | 🔧 Modified | Fixed false positive inflation + webhook env var |
| `mlb-status-monitor-v2.yml` | 🔧 Modified | Webhook env var fix + `false_positive_logged.json` commit |
| `analytics.json` | 🔧 Modified | `false_positives` reset from 406 → 0 |

---

## [2.0.2] - 2026-04-18

### 🔧 Changed

#### `weather-update-v2.yml` — Removed Stale Secret Reference
- Removed `WEATHER_API_KEY` from `Run weather bot` step

#### `test_venues.py` — Full Rewrite for NWS API
- Replaced OpenWeatherMap with NWS API
- Replaced zip codes with lat/lon coordinates
- Organized into 5 clearly labeled sections

#### `test-venues.yml` — Removed Stale Secret Reference
- Removed entire `env` block — NWS needs no API key

### 🗑️ Removed

#### All Remaining `WEATHER_API_KEY` References — Fully Purged
- Zero `WEATHER_API_KEY` references remain anywhere in the repo

### 📋 Files Changed

| File | Type | Summary |
|---|---|---|
| `weather-update-v2.yml` | 🔧 Modified | Removed stale `WEATHER_API_KEY` env var |
| `test_venues.py` | 🔧 Rewritten | Full NWS rewrite |
| `test-venues.yml` | 🔧 Modified | Removed `WEATHER_API_KEY` env block |

---

## [2.0.1] - 2026-04-18

### 🐛 Fixed

#### `high-risk-alert-v2.yml` — Prediction Accuracy Tracking Broken
- **Root cause:** `high_risk_predictions.json` never committed
- **Symptom:** Accuracy dashboard showing 0.0%
- **Fix:** Added `git add high_risk_predictions.json || true`

#### `high-risk-alert-v2.yml` — Stale Secret Reference
- Removed `WEATHER_API_KEY` — no longer needed

#### `analytics.json` — Accuracy Counters Reset
- All counters reset to clean baseline

### 🎯 Impact

- **Prediction accuracy now populates correctly**
- **Full accuracy loop closed end-to-end**

| Step | File | Status |
|---|---|---|
| 1. Game PKs written to config | `update_schedule.py` | ✅ Fixed in v2.0.0 |
| 2. Predictions saved at 10 AM | `high_risk_alert.py` | ✅ Working |
| 3. Predictions committed to repo | `high-risk-alert-v2.yml` | ✅ Fixed in v2.0.1 |
| 4. Delay detected by monitor | `mlb_game_status_monitor.py` | ✅ Working |
| 5. Accuracy logged to analytics | `analytics.py` | ✅ Working |

### 📋 Files Changed

| File | Type | Summary |
|---|---|---|
| `high-risk-alert-v2.yml` | 🔧 Modified | Added predictions file + removed stale key |
| `analytics.json` | 🔧 Modified | Accuracy counters reset |

---

## [2.0.0] - 2026-04-18

### ✨ Added

#### `weather_bot.py` — NWS Stadium Coordinates Dictionary
- New `STADIUM_COORDINATES` dict with lat/lon for all 29 US stadiums
- Replaces city string queries with precise GPS coordinates

#### `weather_bot.py` — NWS Fetch Functions
- New `get_nws_hourly_forecast_url()` — two-step NWS lookup
- `get_weather_forecast()` fully rewritten to use NWS
- Targets exact game start hour

#### `high_risk_alert.py` — NWS Stadium Coordinates Dictionary
- Same `STADIUM_COORDINATES` dict as `weather_bot.py`

#### `update_schedule.py` — Missing Venue Mappings + `game_pk`
- Added `Sutter Health Park`, `Salt River Fields at Talking Stick`,
  `JetBlue Park at Fenway South`
- Removed stale `Oakland Coliseum`
- Added `game_pk` and `venue` fields to every game entry

#### `analytics.py` — NWS References in STATUS.md
- Updated Component Health and System Architecture tables

#### `mlb_game_status_monitor.py` — Request Timeouts
- Added `timeout=10` to all requests

### 🔧 Changed

#### Weather API — OpenWeatherMap → National Weather Service

| Attribute | OpenWeatherMap | NWS API |
|---|---|---|
| Cost | Free (1,000/day limit) | Free — unlimited, no key |
| Accuracy | ~85% | ~92–95% US hourly |
| Granularity | 3-hour buckets | True hourly periods |
| Game time targeting | Closest 3-hr bucket | Exact game start hour |

#### Thresholds — Tightened for NWS Precision

| Threshold | Old | New |
|---|---|---|
| HIGH RISK rain | ≥70% | ≥75% |
| MONITOR rain | ≥40% | ≥45% |
| HIGH RISK cold temp | ≤20°F | ≤35°F |

### 🗑️ Removed

- `WEATHER_API_KEY` GitHub Secret
- Toronto Blue Jays moved from Retractable to Fixed Dome

### 🎯 Impact

- **Forecast accuracy:** ~85% → ~92–95%
- **Exact game-time targeting**
- **Zero API cost change**
- **No API key to manage**

### 📊 Weather API Comparison

| | OpenWeatherMap | NWS |
|---|---|---|
| **Annual Cost** | $0 | $0 |
| **API Key** | Required | Not required |
| **Accuracy** | ~85% | ~92–95% |
| **Granularity** | 3-hour buckets | True hourly |

### 📋 Files Changed

| File | Type | Summary |
|---|---|---|
| `weather_bot.py` | 🔧 Modified | NWS API, coords dict, thresholds |
| `high_risk_alert.py` | 🔧 Modified | NWS API, coords dict, thresholds |
| `update_schedule.py` | 🔧 Modified | `game_pk`, missing venues, timeout |
| `mlb_game_status_monitor.py` | 🔧 Modified | Request timeouts |
| `analytics.py` | 🔧 Modified | OWM → NWS text |

---

## [1.5.0] - 2026-04-16

### ✨ Added

#### `analytics.py` — Auto-Generate `STATUS.md`
- New `generate_status_markdown()` function
- `save_analytics()` now calls both markdown generators
- All three files always stay in sync

#### All Three Workflows — `STATUS.md` Auto-Commit
- Added `git add STATUS.md || true` to all commit steps

### 🎯 Impact
- **`STATUS.md` never goes stale**
- **Zero manual maintenance required**

### 📊 Auto-Update Coverage

| File | Updated By | Frequency |
|---|---|---|
| `analytics.json` | Every workflow run | Real-time |
| `ANALYTICS.md` | `save_analytics()` | Real-time |
| `STATUS.md` | `save_analytics()` ✅ NEW | Real-time |

---

## [1.4.0] - 2026-04-16

### ✨ Added

#### External Cron Trigger via `cron-job.org`
- **Problem:** GitHub Actions cron delayed 30-60 min during peak hours
- **Solution:** `cron-job.org` triggers monitor every 10 min via
  `workflow_dispatch` — bypassing GitHub's unreliable scheduler

### 🎯 Impact
- **Guaranteed 10-minute detection cycles**
- **Rain delays detected within 10 minutes**

### 📊 Monitoring Reliability

| | Before | After |
|---|---|---|
| Trigger source | GitHub cron (unreliable) | cron-job.org (reliable) |
| Typical delay | 30–60 min | ~10 min guaranteed |
| Manual triggers needed | Yes | No |

---

## [1.3.4] - 2026-04-08

### 🐛 Fixed

#### `mlb-status-monitor-v2.yml` — Commit Step Failing with Exit Code 1
- Split `git add` into individual lines with `|| true`
- Removed `git diff --quiet &&` from commit condition
- Added `|| true` to `git commit`

### 🎯 Impact
- Commit step no longer fails the job

---

## [1.3.3] - 2026-04-08

### 🐛 Fixed
- All Three Workflows — Skipped Run Analytics Not Logged
- `weather-update-v2.yml` — Analytics Never Committed
- `high_risk_alert.py` — Games Monitored Double Counting

### 🎯 Impact
- Skipped Runs now accurately tracked
- Games Monitored no longer double counted

---

## [1.3.2] - 2026-04-08

### ✨ Added
- `high_risk_alert.py` — Games Monitored Tracking
- `mlb-status-monitor-v2.yml` — Skipped Run Tracking
- `analytics.py` — Accurate Key Insights Calculations

### 🐛 Fixed
- Analytics Dashboard — all metrics showing incorrect values

---

## [1.3.1] - 2026-04-08

### ✨ Added
- `high_risk_alert.py` — `save_high_risk_predictions()`
- `mlb_game_status_monitor.py` — `check_and_log_prediction_accuracy()`
- `mlb_game_status_monitor.py` — `check_and_log_false_positives()`
- `mlb-status-monitor-v2.yml` — Predictions File Persistence

### 🎯 Impact
- Prediction Accuracy dashboard now populates automatically

---

## [1.3.0] - 2026-04-08

### 🐛 Fixed
- CRITICAL: "RAIN DELAY DETECTED" firing on Postponed games
- CRITICAL: Duplicate alerts every 10 minutes
- CRITICAL: `game_states.json` not persisting between runs
- Added `STATE_SUSPENDED` handling

### 🎯 Impact
- Zero duplicate alerts
- Correct alert types
- State survives across GitHub Actions runs

---

## [1.2.2] - 2026-04-08

### 🔧 Changed
- Retractable Roof Unknown Status: Unknown → Skip

---

## [1.2.1] - 2026-03-29

### 🔧 Changed
- Cold temp HIGH RISK threshold: 35°F → 20°F

---

## [1.2.0] - 2026-03-28

### ✨ Added
- Roof-Aware Weather Filtering
- Fixed domes excluded, retractable roofs checked via MLB API
- ~27% reduction in false alerts

---

## [1.1.1] - 2026-03-26

### 🔧 Fixed
- Analytics not updating — added missing git commit steps
- Added game status analytics tracking to `mlb_game_status_monitor.py`
```

---

## ✅ What Was Fixed in This File

| Issue | Fix |
|---|---|
| `[2.0.8]` completely missing | ✅ Added |
| `[2.0.9]` had broken code block that swallowed `[2.0.8]` | ✅ Fixed |
| `[2.0.5]` had broken code block sample | ✅ Removed — replaced with clean text |
| Older entries condensed | ✅ Kept all content, removed redundancy |

Paste and commit! 🚀
