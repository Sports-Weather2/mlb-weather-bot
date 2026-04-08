# Changelog

All notable changes to the MLB Weather Monitoring System.

The format is based on [Keep a Changelog](https://keepachangelog.com/).

---

## [1.3.1] - 2026-04-08

### ✨ Added

#### `high_risk_alert.py` — Prediction Accuracy Tracking
- **New function `save_high_risk_predictions()`**: Saves today's high-risk predicted
  game PKs to `high_risk_predictions.json` so the MLB status monitor can
  cross-reference actual delays and calculate real prediction accuracy
  - Called automatically in `main()` whenever high-risk games are found
  - Keyed by date to prevent yesterday's predictions from polluting today's accuracy

#### `mlb_game_status_monitor.py` — Prediction Accuracy Tracking
- **New function `check_and_log_prediction_accuracy()`**: When an actual
  delay or postponement fires, cross-references against saved predictions
  and logs the result to analytics
  - `TRUE POSITIVE` — game was predicted high-risk AND actually delayed ✅
  - `FALSE NEGATIVE` — delay occurred but was not predicted ❌
  - Handles missing predictions file gracefully (logs as false negative)
- **New function `check_and_log_false_positives()`**: At the end of each
  monitoring cycle, checks any predicted games that finished without a
  delay and logs them as false positives
  - Called once per cycle after all games are processed
  - Only runs if `high_risk_predictions.json` exists for today

#### `mlb-status-monitor-v2.yml` — Predictions File Persistence
- Added `high_risk_predictions.json` to the git commit step so prediction
  data persists between GitHub Actions runs and is available for
  cross-referencing when actual delays occur

### 🔧 Changed

#### `mlb_game_status_monitor.py`
- Updated import to include `log_prediction_accuracy` from `analytics.py`
- `monitor_games()` now calls `check_and_log_prediction_accuracy()` when
  a `STATE_DELAYED` or `STATE_POSTPONED` alert fires
- `monitor_games()` now calls `check_and_log_false_positives()` at the
  end of every monitoring cycle before saving game states

### 🎯 Impact
- **Prediction Accuracy dashboard now populates automatically** — Actual
  Delays Occurred, Correctly Predicted, False Positives and False Negatives
  will all update in real-time as games are monitored
- **No manual entry required** — the two scripts communicate via
  `high_risk_predictions.json` without any human intervention
- **Full accuracy loop closed**: High-risk prediction → actual delay
  detection → accuracy logged → dashboard updated

### 📊 Accuracy Tracking Flow

| Step | File | Action |
|---|---|---|
| 1️⃣ Prediction saved | `high_risk_alert.py` | Writes `high_risk_predictions.json` at 10 AM |
| 2️⃣ Actual delay detected | `mlb_game_status_monitor.py` | Reads predictions, calls `log_prediction_accuracy()` |
| 3️⃣ False positives checked | `mlb_game_status_monitor.py` | End of cycle check for predicted games with no delay |
| 4️⃣ State + predictions persisted | `mlb-status-monitor-v2.yml` | Commits both `game_states.json` + `high_risk_predictions.json` |

---

## [1.3.0] - 2026-04-08

### 🐛 Fixed

#### `mlb_game_status_monitor.py` — Duplicate Alert & Wrong Alert Type Bugs
- **CRITICAL: "RAIN DELAY DETECTED" firing on already-Postponed games**
  - **Root cause:** `is_weather_delay()` included `'postponed'` in `delay_keywords`,
    causing Postponed games to match the DELAY check before the POSTPONED check
  - **Fix:** Split into two separate functions — `is_active_weather_delay()`
    explicitly excludes Postponed/Suspended states, and `is_postponed()` /
    `is_suspended()` handle those states independently
  - **Fix:** Reordered check priority — POSTPONED is now evaluated **before**
    DELAY so a Postponed game can never be mislabeled as a Rain Delay

- **CRITICAL: Duplicate alerts firing every 10 minutes for the same game/status**
  - **Root cause:** `game_states.json` was never actually read from the previous
    run — GitHub Actions spins up a fresh VM each run, and without a `git pull`
    after checkout, the committed state file was invisible to subsequent runs
  - **Fix:** Added `normalize_api_state()` to convert raw MLB API values
    (`"Live"`, `"Preview"`, `"Final"`) into consistent internal constants
    (`STATE_LIVE`, `STATE_PREVIEW`, `STATE_FINAL`), preventing comparison
    mismatches

- **Inconsistent state value storage**
  - **Root cause:** Some states were stored as hardcoded strings (`'DELAYED'`,
    `'LIVE'`, `'POSTPONED'`) while others stored raw API values, making
    comparisons unreliable
  - **Fix:** Introduced normalized state constants (`STATE_DELAYED`,
    `STATE_POSTPONED`, `STATE_LIVE`, `STATE_FINAL`, `STATE_PREVIEW`,
    `STATE_SUSPENDED`) used consistently throughout all read/write/compare
    operations

- **Added `STATE_SUSPENDED` handling**
  - Suspended games were previously unhandled and would fall through all
    checks silently
  - Now detected via `is_suspended()` and alerts via new `STATE_SUSPENDED`
    alert type

#### `mlb-status-monitor-v2.yml` — State Persistence Failure
- **CRITICAL: `game_states.json` not persisting between GitHub Actions runs**
  - **Root cause:** `actions/checkout@v3` without `fetch-depth: 0` and no
    subsequent `git pull` meant each run checked out a stale snapshot, never
    seeing the state file committed by the previous run — every run behaved
    as if no games had ever been seen
  - **Fix:** Added `fetch-depth: 0` to checkout and a dedicated **"Pull latest
    state from repo"** step immediately after checkout using
    `git pull --rebase origin main`
  - **Fix:** Added `git pull --rebase` before `git push` in the commit step
    to handle concurrent run conflicts instead of silently dropping state
    with `|| true`
  - **Fix:** Replaced silent `git push || true` with a push warning echo so
    state loss is visible in run logs:
    `⚠️ WARNING: Push failed — game state may not persist to next run`

#### `high-risk-alert-v2.yml` — Duplicate High Risk Alert Potential
- **`git push || true` silently swallowing push failures**
  - If two cron runs overlapped and the push failed, `last_high_risk_run.txt`
    was never saved, causing the deduplication check to fail and a second
    alert to fire
  - **Fix:** Added `git pull --rebase origin main` before push and replaced
    silent failure with a warning echo

### 🔧 Changed

#### `mlb_game_status_monitor.py`
- Refactored `is_weather_delay()` into three focused functions:
  - `is_weather_related(reason, detailed_state)` — pure weather keyword
    check, no state logic
  - `is_active_weather_delay(game_status)` — in-game delay only, explicitly
    excludes Postponed/Suspended
  - `is_postponed(game_status)` — dedicated Postponed state check
  - `is_suspended(game_status)` — dedicated Suspended state check
- Added `normalize_api_state()` to map raw MLB API `abstractGameState` /
  `detailedState` values to internal constants
- `monitor_games()` check order now enforces:
  **POSTPONED → SUSPENDED → DELAY → RESUME → no change**
- State stored in `game_states.json` now always uses normalized constants,
  never raw API strings
- `save_game_states()` now writes with `indent=2` for human-readable state
  file (easier debugging in GitHub repo browser)

#### `mlb-status-monitor-v2.yml`
- Added `fetch-depth: 0` to `actions/checkout@v3`
- Added **"Pull latest state from repo"** step after checkout with state
  file preview
- Extended `git push` failure handling from silent `|| true` to warning echo
- Monitoring window hard cutoff at 22:00 PT intentionally maintained —
  reduces noise after West Coast prime-time games complete

#### `high-risk-alert-v2.yml`
- Added `git pull --rebase` before push in commit step
- Replaced `git push || true` with warning echo on failure
- Added `2>/dev/null || true` to `git add` for analytics files to suppress
  errors if files don't exist on first run

### 🎯 Impact
- **Zero duplicate alerts** for Postponed or Delayed games — each state
  change alerts exactly once regardless of how many monitoring runs follow
- **Correct alert types** — a Postponed game now always shows
  `📅 GAME POSTPONED`, never `🚨 RAIN DELAY DETECTED`
- **State survives across GitHub Actions runs** — `game_states.json` is
  reliably read and written between the 10-minute monitoring cycles
- **Transparent failures** — push failures now visible in Actions logs
  instead of silently breaking the deduplication system

### 📊 Alert Firing Behavior (After Fix)

| Scenario | Before Fix | After Fix |
|---|---|---|
| Game Postponed — first detection | 🚨 RAIN DELAY (wrong) | 📅 GAME POSTPONED (correct) ✅ |
| Game Postponed — next 10-min run | 🚨 RAIN DELAY again (duplicate) | Silent — no alert ✅ |
| Game Postponed — all subsequent runs | Repeated every 10 min all day | Silent — no alert ✅ |
| Active in-game rain delay | 🚨 RAIN DELAY (correct but repeated) | 🚨 RAIN DELAY once only ✅ |
| Delay lifted, game resumes | ✅ GAME RESUMING (repeated) | ✅ GAME RESUMING once only ✅ |
| Game Suspended | No alert (fell through) | ⏸️ GAME SUSPENDED once only ✅ |

---

## [1.2.2] - 2026-04-08

### 🔧 Changed
- **Retractable Roof Unknown Status Handling**: Changed behavior when
  retractable roof status cannot be determined
  - **Previous behavior:** Unknown roof status = Alert (conservative,
    more false positives)
  - **New behavior:** Unknown roof status = Skip alert (reduces false
    positives)
  - Applies to all 6 retractable roof stadiums (Chase Field, loanDepot
    park, Globe Life Field, Minute Maid Park, T-Mobile Park, American
    Family Field)
  - Roof confirmed OPEN = Still alerts (correct behavior maintained)
  - Roof confirmed CLOSED = Still skips (correct behavior maintained)

### 🎯 Impact
- **Reduced false positives**: Retractable roof games no longer alert
  when MLB API doesn't provide roof status
- **Example:** Miami Marlins with 100% rain but unknown roof status will
  now be skipped (no false alert)
- **Better efficiency**: Fewer unnecessary alerts for operations teams
  to review
- **Trade-off:** Slight increase in missed alerts IF roof is actually
  open but API doesn't report it (rare scenario)
- **Updated files**: `weather_bot.py` and `high_risk_alert.py` —
  `get_roof_status_from_mlb()` function

### 📊 New Alert Behavior for Retractable Roofs

| MLB API Response | Alert Behavior |
|---|---|
| Roof = Open | ✅ Alert (weather can impact game) |
| Roof = Closed | ⏭️ Skip (protected from weather) |
| Roof = Unknown/Not provided | ⏭️ Skip (assume closed) — NEW |
| API Error | ⏭️ Skip (assume closed) — NEW |

### 🔍 Enhanced Logging
Console output now shows specific roof status decisions:
- `🔓 [Venue] roof confirmed OPEN - including in alert`
- `🔒 [Venue] roof confirmed CLOSED - skipping alert`
- `❓ [Venue] roof status unknown - assuming closed, skipping alert` (NEW)

---

## [1.2.1] - 2026-03-29

### 🔧 Changed
- **Cold Temperature Threshold Adjustment**: Lowered HIGH RISK cold
  temperature threshold from 35°F to 20°F
  - Reduces false HIGH RISK alerts for typical early-season cold games
    (30–35°F)
  - MLB games regularly play in 30s°F range without delays
  - Only extremely rare conditions (≤20°F) now trigger HIGH RISK red
    alerts
  - Games 21–34°F will now show as MONITOR (yellow) instead of HIGH
    RISK (red)

### 🎯 Impact
- **Fewer false positives**: Today's 30–33°F games would no longer
  trigger HIGH RISK
- **Better alert accuracy**: HIGH RISK reserved for truly dangerous
  conditions
- **Improved user trust**: Red alerts only for conditions likely to
  cause actual delays
- **Updated files**: `weather_bot.py` and `high_risk_alert.py`
  IMPACT_RULES

### 📊 Alert Thresholds (Updated)
**HIGH RISK (🔴):**
- Temperature ≤20°F OR ≥100°F (changed from ≤35°F)
- Rain ≥70%
- Thunderstorms present
- Wind gusts ≥30 mph

**MONITOR (🟡):**
- Temperature 21–39°F OR 96–99°F (expanded cold range)
- Rain 40–69%
- Wind sustained 15–29 mph

---

## [1.2.0] - 2026-03-28

### ✨ Added
- **Roof-Aware Weather Filtering**: Intelligent stadium roof detection
  to reduce false weather alerts
  - Fixed dome stadiums (Tropicana Field, Rogers Centre) automatically
    excluded from weather forecasts
  - Retractable roof stadiums (Chase Field, loanDepot park, Globe Life
    Field, Minute Maid Park, T-Mobile Park, American Family Field)
    checked via MLB API for open/closed status
  - Only alerts for games where weather can actually impact play
  - Reduces noise by ~27% (8 of 30 MLB stadiums have roof protection)

### 🔄 Changed
- **`weather_bot.py`**: Added roof filtering before weather API calls
  - New functions: `get_venue_name_from_location()`,
    `get_venue_roof_info()`, `get_roof_status_from_mlb()`
  - Filters games by roof status before fetching weather data
  - Saves weather API calls for games in closed/domed stadiums
  - Enhanced console logging shows which games are skipped and why

- **`high_risk_alert.py`**: Added roof filtering for 10 AM high-risk
  alerts
  - Same roof detection logic as weather bot
  - Only alerts for games vulnerable to weather impacts
  - Reduces false positives for operations teams

- **`mlb_game_status_monitor.py`**: Enhanced real-time monitoring with
  roof context
  - Monitors ALL games regardless of roof (delays can happen for
    non-weather reasons)
  - Adds venue name and roof type (🏟️ Fixed Dome / 🔄 Retractable /
    ☀️ Open Air) to delay alerts
  - Includes smart operational notes for unexpected delays at roofed
    stadiums
  - Helps ops distinguish weather vs. non-weather issues

### 🎯 Impact
- **Reduced alert noise**: Eliminates unnecessary weather alerts for
  games protected by closed roofs
- **Better operational accuracy**: Roof context helps teams understand
  delay causes
- **Smarter resource usage**: Fewer weather API calls for games that
  don't need monitoring
- **Safer defaults**: If roof status unknown or API fails, system
  defaults to alerting (conservative approach)

### 📋 Stadium Coverage
- **Fixed Domes (2)**: Always excluded from weather forecasts
- **Retractable Roofs (6)**: Dynamically checked via MLB API
- **Open-Air (22)**: Always monitored for weather impacts

---

## [1.1.1] - 2026-03-26

### 🔧 Fixed
- **Analytics Not Updating**: Fixed critical issue where `ANALYTICS.md`
  was not updating since March 21, 2026
  - Added missing git commit steps to all three workflow files to push
    analytics updates back to GitHub
  - Analytics data (`analytics.json` and `ANALYTICS.md`) now properly
    persists after each workflow run
  - Real-time tracking now functional for all alert types

### ✨ Added
- **Game Status Analytics**: Added analytics tracking to
  `mlb_game_status_monitor.py`
  - Rain delay alerts now logged to analytics
  - Game resumption alerts now logged to analytics
  - Postponement alerts now logged to analytics
  - Workflow success/failure tracking added

### 🔄 Changed
- **Workflow Files Updated**:
  - `weather-update.yml`: Added new analytics commit step to include
    `analytics.json` and `ANALYTICS.md`
  - `high-risk-alert.yml`: Updated existing commit step to include
    `analytics.json` and `ANALYTICS.md`
  - `mlb-status-monitor.yml`: Updated existing commit step to include
    `analytics.json` and `ANALYTICS.md`

- **Python Scripts**:
  - `mlb_game_status_monitor.py`: Integrated `log_alert()` and
    `log_workflow_run()` functions

### 🎯 Impact
- `ANALYTICS.md` will now update in real-time after each workflow run
- All six alert types now properly tracked: daily reports, high-risk
  alerts, delays, resumptions, postponements
- System performance and accuracy metrics now reliably captured
