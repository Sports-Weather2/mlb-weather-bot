# 📊 System Analytics

**MLB Weather Monitoring System**

---

## 🟢 CURRENT PERFORMANCE

**Status:** Fully Operational  
**Last Updated:** March 27, 2026 10:15 PM PT  
**Season:** Regular Season 2026

---

## ⚠️ Important Methodology Change - March 28, 2026

**Starting March 28, 2026, the system implements intelligent roof-aware filtering:**

### What Changed:
- 🏟️ Fixed dome stadiums (2) automatically excluded from weather forecasts
- 🔄 Retractable roof stadiums (6) only monitored when roof is open or status unknown
- ☀️ Open-air stadiums (22) always monitored

### Impact on Metrics:
- **"Games Monitored"** count will be ~27% lower for forecast reports (Daily & High-Risk)
- **This is expected behavior** and improves alert accuracy
- Real-time delay/postponement tracking still covers ALL games
- Analytics now reflect **games that can actually be weather-impacted**

### Why This Matters:
This change reduces false weather alerts while maintaining 100% accuracy for games where weather can cause delays. If you're comparing historical data:
- **Before March 28:** All 30 teams monitored for weather
- **After March 28:** Only games vulnerable to weather conditions (typically 22-28 games per day)

---

## 📈 Overall Statistics

| Metric | Count |
|--------|-------|
| 📅 Games Monitored | 0 |
| 📬 Total Alerts Sent | 1 |
| 📊 Daily Reports | 0 |
| 🚨 High-Risk Alerts | 1 |
| ⏸️ Delay Alerts | 0 |
| ▶️ Resumption Alerts | 0 |
| 📅 Postponement Alerts | 0 |

**Note:** "Games Monitored" reflects roof-aware filtering starting March 28, 2026.

---

## 🎯 Prediction Accuracy

| Metric | Value |
|--------|-------|
| Actual Delays Occurred | 0 |
| Correctly Predicted | 0 |
| **Accuracy Rate** | **0.0%** |
| False Positives | 0 |
| False Negatives | 0 |

---

## 🔧 System Reliability

| Metric | Count | Percentage |
|--------|-------|------------|
| Total Workflow Runs | 13 | - |
| ✅ Successful | 13 | 100.0% |
| ❌ Failed | 0 | 0.0% |
| ⏭️ Skipped (time check) | 0 | 0.0% |

**System Uptime:** 100.0%

---

## 🏟️ Stadium Coverage Breakdown

_(Available starting March 28, 2026)_

| Roof Type | Stadiums | Weather Monitoring | Delay Monitoring |
|-----------|----------|-------------------|------------------|
| ☀️ Open-Air | 22 | ✅ Always | ✅ Always |
| 🔄 Retractable | 6 | ✅ When open | ✅ Always |
| 🏟️ Fixed Dome | 2 | ❌ Never | ✅ Always |

**Smart Filtering Impact:**
- Reduces unnecessary weather API calls
- Eliminates false positives for protected games
- Maintains operational safety with real-time delay monitoring for all games

---

## 📅 Recent Activity

### Today (March 27, 2026)

- 📊 Alerts sent: 1
- 📅 Games monitored: 0

### Yesterday (March 26, 2026)

- 📊 Alerts sent: 0
- 📅 Games monitored: 0

---

## 💡 Key Insights

**Time Saved:** ~1 hours this season  
**Estimated Value:** $42 in operational efficiency

**Days Active:** 1  
**Average Alerts/Day:** 1.0

**Alert Noise Reduction:** ~27% (starting March 28, 2026 with roof-aware filtering)

---

## 📊 Historical Comparison Guide

When analyzing trends across the March 28 methodology change:

**For Weather Forecasts (Daily & High-Risk Alerts):**
- Compare "alert accuracy" rather than raw game counts
- Focus on "false positive rate" improvements
- Expect lower "games monitored" after March 28 (this is good!)

**For Real-Time Delay Monitoring:**
- No change in coverage (still monitors all games)
- Metrics remain directly comparable before/after March 28

---

## 🔄 Data Updates

This file is automatically updated by `analytics.py` after each workflow run.

**Update Frequency:** Real-time (after each alert sent)

---

## 🔗 Related Documentation

- [Changelog](CHANGELOG.md) - Version history and feature updates
- [Status](STATUS.md) - Current system health and component status
- [User Guide](https://confluence.dtveng.net/spaces/~le805s/pages/793701279/) - Full documentation

---

_Last generated: March 27, 2026 10:15 PM PT_
