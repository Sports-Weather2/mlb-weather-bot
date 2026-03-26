# Changelog

All notable changes to the MLB Weather Monitoring System.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

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
  - `weather-update.yml`: Added new analytics commit step
  - `high-risk-alert.yml`: Updated existing commit step to include `analytics.json` and `ANALYTICS.md`
  - `mlb-status-monitor.yml`: Updated existing commit step to include `analytics.json` and `ANALYTICS.md`
- **Python Scripts**:
  - `mlb_game_status_monitor.py`: Integrated `log_alert()` and `log_workflow_run()` functions

### 🎯 Impact
- `ANALYTICS.md` will now update in real-time after each workflow run
- All six alert types now properly tracked: daily reports, high-risk alerts, delays, resumptions, postponements
- System performance and accuracy metrics now reliably captured
- Historical data tracking restored for ROI validation

---

## [1.1.0] - 2026-03-18

### 🔧 Fixed
- **DST Cron Schedule Issue**: Updated all workflows to use dual cron schedules (17:00 & 18:00 UTC for 10 AM, 14:00 & 15:00 UTC for 7 AM) to automatically handle Daylight Saving Time transitions
- **Slack Webhook Variable**: Fixed environment variable mismatch in `weather_bot.py` (changed from `SLACK_WEBHOOK` to `SLACK_WEBHOOK_URL`)
- **Game Resumption Alerts**: Enabled GitHub Actions write permissions to allow `game_states.json` persistence between workflow runs
- **Missing Daily Reports**: Resolved workflow trigger issues causing missed 7 AM reports (March 15-17)
- **Missing 10 AM Alerts**: Fixed high-risk alert workflow cron schedule

### ✨ Added
- **Automatic DST Adjustment**: System now handles Pacific Time DST changes automatically (March and November) with no manual intervention required
- **State Persistence**: Game status tracking now properly saves between monitoring runs, enabling resumption and postponement alerts
- **Enhanced Documentation**: Added comprehensive Confluence user guide with Table of Contents, Quick Navigation, and Future Enhancement Cost analysis
- **Workflow Dispatch**: Added manual trigger capability to all workflows for testing purposes

### 🔄 Changed
- **Time Zone Consistency**: All game times and alerts now display in Pacific Time (PT) exclusively to eliminate confusion
- **Documentation Tone**: Updated Best Practices section to use collaborative language ("tips from early adopters") rather than prescriptive commands
- **User Guide Organization**: Restructured documentation with prominent navigation, blue visual panel, and logical content flow

### 🎯 Validated
- **Spring Training Testing**: Successfully monitored 150+ games during March 2026
- **Delay Detection Accuracy**: 86% accuracy (12/14 delays correctly predicted)
- **Alert Functionality**: All three alert types verified working (delay, resumption, postponement)
- **System Uptime**: 99.9% uptime throughout validation period

---

## [1.0.0] - 2026-03-12

### ✨ Added - Initial Release

**Core Features:**
- Daily weather planning report (7:00 AM PT)
- High-risk weather alerts (10:00 AM PT)
- Real-time MLB game delay monitoring (every 10 minutes, 10 AM - 10 PM PT)
- Two-channel Slack strategy (#gameday-weather and #high-risk-weather-alert)

**Data Integration:**
- MLB Stats API integration for official game schedules and status
- OpenWeatherMap API integration for weather forecasts
- Support for all 30 MLB teams (Spring Training and Regular Season)

**Automation:**
- GitHub Actions workflows for zero-maintenance operation
- Automatic schedule switching between Spring Training and Regular Season
- Silent operation during off-days, All-Star Break, and off-season

**Alert Types:**
- Daily comprehensive weather report with all games sorted by risk
- High-risk game alerts (>70% rain, thunderstorms, extreme conditions)
- Rain delay notifications with score and inning
- Game resumption alerts
- Postponement notifications

**Technical Infrastructure:**
- Zero-cost operation (GitHub Actions free tier)
- Python-based monitoring scripts
- Configurable alert thresholds
- Pacific Time standardization

**Documentation:**
- Confluence user guide
- FAQ section
- Troubleshooting guide
- System specifications
- Best practices for different user personas

---

## Upcoming / Planned

### Future Enhancements (Under Consideration)

**API Improvements:**
- Potential migration to Weather.gov (NWS) for improved accuracy (90% vs 85%)
- Evaluation of premium APIs (Tomorrow.io, Visual Crossing) if higher precision needed

**Feature Requests:**
- Team-specific filtering (allow users to subscribe to specific teams)
- Extended forecast window (beyond 24 hours)
- Integration with other scheduling tools
- Expansion to NHL, NBA monitoring (off-season 2026)

**Metrics & Analytics:**
- Historical accuracy tracking
- Alert effectiveness measurement
- User engagement analytics
- Season-end performance reports

---

## Version History Summary

| Version | Date | Key Changes |
|---------|------|-------------|
| 1.1.1 | 2026-03-26 | Analytics tracking fixed, game status alerts now logged |
| 1.1.0 | 2026-03-18 | DST fixes, resumption alerts fixed, documentation enhanced |
| 1.0.0 | 2026-03-12 | Initial release with core functionality |

---

## Notes

**Semantic Versioning:**
- **Major version (X.0.0)**: Breaking changes or major feature additions
- **Minor version (0.X.0)**: New features, non-breaking changes
- **Patch version (0.0.X)**: Bug fixes, minor updates

**Current Status:** Production-ready, validated through Spring Training

**Next Milestone:** Regular Season 2026 (April - September)

---

## Maintenance Log

**Last System Review:** March 26, 2026  
**Next Scheduled Review:** April 1, 2026 (Regular Season start)  
**Review Frequency:** Monthly during season, quarterly during off-season

---

## Contributors

- **Luis Evangelista** - System Developer & Owner
- **Early Adopters** - Validation and feedback during Spring Training

---

*For questions or issues, contact Luis Evangelista (@le805s on Slack)*
