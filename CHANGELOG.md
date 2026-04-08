# Changelog

All notable changes to the MLB Weather Monitoring System.

The format is based on [Keep a Changelog](https://keepachangelog.com/).

---

## [1.2.2] - 2026-04-08

### 🔧 Changed
- **Retractable Roof Unknown Status Handling**: Changed behavior when retractable roof status cannot be determined
  - **Previous behavior:** Unknown roof status = Alert (conservative, more false positives)
  - **New behavior:** Unknown roof status = Skip alert (reduces false positives)
  - Applies to all 6 retractable roof stadiums (Chase Field, loanDepot park, Globe Life Field, Minute Maid Park, T-Mobile Park, American Family Field)
  - Roof confirmed OPEN = Still alerts (correct behavior maintained)
  - Roof confirmed CLOSED = Still skips (correct behavior maintained)

### 🎯 Impact
- **Reduced false positives**: Retractable roof games no longer alert when MLB API doesn't provide roof status
- **Example:** Miami Marlins with 100% rain but unknown roof status will now be skipped (no false alert)
- **Better efficiency**: Fewer unnecessary alerts for operations teams to review
- **Trade-off:** Slight increase in missed alerts IF roof is actually open but API doesn't report it (rare scenario)
- **Updated files**: `weather_bot.py` and `high_risk_alert.py` - `get_roof_status_from_mlb()` function

### 📊 New Alert Behavior for Retractable Roofs:

| MLB API Response | Alert Behavior |
|------------------|----------------|
| Roof = Open | ✅ Alert (weather can impact game) |
| Roof = Closed | ⏭️ Skip (protected from weather) |
| Roof = Unknown/Not provided | ⏭️ Skip (assume closed) - NEW |
| API Error | ⏭️ Skip (assume closed) - NEW |

### 🔍 Enhanced Logging:
Console output now shows specific roof status decisions:
- `🔓 [Venue] roof confirmed OPEN - including in alert`
- `🔒 [Venue] roof confirmed CLOSED - skipping alert`  
- `❓ [Venue] roof status unknown - assuming closed, skipping alert` (NEW)

---

## [1.2.1] - 2026-03-29

### 🔧 Changed
- **Cold Temperature Threshold Adjustment**: Lowered HIGH RISK cold temperature threshold from 35°F to 20°F
  - Reduces false HIGH RISK alerts for typical early-season cold games (30-35°F)
  - MLB games regularly play in 30s°F range without delays
  - Only extremely rare conditions (≤20°F) now trigger HIGH RISK red alerts
  - Games 21-34°F will now show as MONITOR (yellow) instead of HIGH RISK (red)

### 🎯 Impact
- **Fewer false positives**: Today's 30-33°F games would no longer trigger HIGH RISK
- **Better alert accuracy**: HIGH RISK reserved for truly dangerous conditions
- **Improved user trust**: Red alerts only for conditions likely to cause actual delays
- **Updated files**: `weather_bot.py` and `high_risk_alert.py` IMPACT_RULES

### 📊 Alert Thresholds (Updated)
**HIGH RISK (🔴):**
- Temperature ≤20°F OR ≥100°F (changed from ≤35°F)
- Rain ≥70%
- Thunderstorms present
- Wind gusts ≥30 mph

**MONITOR (🟡):**
- Temperature 21-39°F OR 96-99°F (expanded cold range)
- Rain 40-69%
- Wind sustained 15-29 mph

---

## [1.2.0] - 2026-03-28

### ✨ Added
- **Roof-Aware Weather Filtering**: Intelligent stadium roof detection to reduce false weather alerts
  - Fixed dome stadiums (Tropicana Field, Rogers Centre) automatically excluded from weather forecasts
  - Retractable roof stadiums (Chase Field, loanDepot park, Globe Life Field, Minute Maid Park, T-Mobile Park, American Family Field) checked via MLB API for open/closed status
  - Only alerts for games where weather can actually impact play
  - Reduces noise by ~27% (8 of 30 MLB stadiums have roof protection)

### 🔄 Changed
- **`weather_bot.py`**: Added roof filtering before weather API calls
  - New functions: `get_venue_name_from_location()`, `get_venue_roof_info()`, `get_roof_status_from_mlb()`
  - Filters games by roof status before fetching weather data
  - Saves weather API calls for games in closed/domed stadiums
  - Enhanced console logging shows which games are skipped and why

- **`high_risk_alert.py`**: Added roof filtering for 10 AM high-risk alerts
  - Same roof detection logic as weather bot
  - Only alerts for games vulnerable to weather impacts
  - Reduces false positives for operations teams

- **`mlb_game_status_monitor.py`**: Enhanced real-time monitoring with roof context
  - Monitors ALL games regardless of roof (delays can happen for non-weather reasons)
  - Adds venue name and roof type (🏟️ Fixed Dome / 🔄 Retractable / ☀️ Open Air) to delay alerts
  - Includes smart operational notes for unexpected delays at roofed stadiums
  - Helps ops distinguish weather vs. non-weather issues

### 🎯 Impact
- **Reduced alert noise**: Eliminates unnecessary weather alerts for games protected by closed roofs
- **Better operational accuracy**: Roof context helps teams understand delay causes
- **Smarter resource usage**: Fewer weather API calls for games that don't need monitoring
- **Safer defaults**: If roof status unknown or API fails, system defaults to alerting (conservative approach)

### 📋 Stadium Coverage
- **Fixed Domes (2)**: Always excluded from weather forecasts
- **Retractable Roofs (6)**: Dynamically checked via MLB API
- **Open-Air (22)**: Always monitored for weather impacts

---

## [1.1.1] - 2026-03-26

### 🔧 Fixed
- **Analytics Not Updating**: Fixed critical issue where `ANALYTICS.md` was not updating since March 21, 2026
  - Added missing git commit steps to all three workflow files to push analytics updates back to GitHub
  - Analytics data (`analytics.json` and `ANALYTICS.md`) now properly persists after each workflow run
  - Real-time tracking now functional for all alert types

### ✨ Added
- **Game Status Analytics**: Added analytics tracking to `mlb_game_status_monitor.py`
  - Rain delay alerts now logged to analytics
  - Game resumption alerts now logged to analytics
  - Postponement alerts now logged to analytics
  - Workflow success/failure tracking added

### 🔄 Changed
- **Workflow Files Updated**:
  - `weather-update.yml`: Added new analytics commit step to include `analytics.json` and `ANALYTICS.md`
  - `high-risk-alert.yml`: Updated existing commit step to include `analytics.json` and `ANALYTICS.md`
  - `mlb-status-monitor.yml`: Updated existing commit step to include `analytics.json` and `ANALYTICS.md`

- **Python Scripts**:
  - `mlb_game_status_monitor.py`: Integrated `log_alert()` and `log_workflow_run()` functions

### 🎯 Impact
- `ANALYTICS.md` will now update in real-time after each workflow run
- All six alert types now properly tracked: daily reports, high-risk alerts, delays, resumptions, postponements
- System performance and accuracy metrics now reliably captured
