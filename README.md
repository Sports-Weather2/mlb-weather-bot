# 🌤️ MLB Weather Monitoring System

**Automated weather alerts for MLB broadcast operations**

---

## 📊 Overview

Fully automated weather monitoring system that tracks conditions for all MLB games and sends real-time alerts to Slack channels. Designed to support broadcast operations teams with daypart scheduling and EPG/guide listing adjustments.

---

## ✨ Features

- **📅 Daily Weather Reports** - Comprehensive morning overview at 7:00 AM PT
- **🚨 High-Risk Alerts** - Mid-morning check at 10:00 AM PT for games needing attention
- **⏱️ Real-Time Monitoring** - Live rain delay notifications during game hours (10 AM - 10 PM PT)
- **🌍 Automatic DST Handling** - Seamlessly switches between Standard and Daylight Saving Time
- **💰 Zero Cost** - Built on GitHub Actions free tier with free API services
- **🔧 Zero Maintenance** - Fully automated, no manual intervention required

---

## 📱 Slack Channels

### **#gameday-weather**
Daily reference channel for morning planning
- Posts at 7:00 AM PT
- Shows all games for next 24 hours
- Games sorted by risk level (High → Clear)

### **#high-risk-weather-alert**
Urgent action channel for critical weather
- Posts at 10:00 AM PT (high-risk games only)
- Real-time rain delay/postponement alerts
- @channel mentions for visibility

---

## 📚 Documentation

**Full User Guide:** [Confluence Documentation](https://confluence.dtveng.net/spaces/~le805s/pages/793701279/MLB+Weather+Monitoring+System+-+User+Guide)

Includes:
- Quick start guide
- Daily workflow instructions
- Alert type explanations
- Troubleshooting tips
- FAQ

---

## 🛠️ Technical Stack

| Component | Technology |
|-----------|-----------|
| **Platform** | GitHub Actions |
| **Language** | Python 3.10 |
| **MLB Data** | MLB Stats API (Official) |
| **Weather** | OpenWeatherMap API |
| **Alerts** | Slack Webhooks |
| **Schedule** | Cron (UTC-based, PT-adjusted) |

---

## 🔄 Automated Workflows

### **Daily Weather Report** (`weather-update.yml`)
- **Schedule:** 7:00 AM PT daily
- **Function:** Comprehensive weather overview for all games
- **Output:** #gameday-weather channel

### **High Risk Weather Alerts** (`high-risk-alert.yml`)
- **Schedule:** 10:00 AM PT daily
- **Function:** Urgent alerts for high-risk games (>70% rain, thunderstorms, extreme conditions)
- **Output:** #high-risk-weather-alert channel

### **MLB Game Status Monitor** (`mlb-status-monitor.yml`)
- **Schedule:** Every 10 minutes (10 AM - 10 PM PT)
- **Function:** Real-time rain delay and postponement detection
- **Output:** #high-risk-weather-alert channel

### **Test Venue Locations** (`test-venues.yml`)
- **Schedule:** Manual only
- **Function:** Validates weather API access for all MLB stadiums

---

## 🎯 Use Cases

**For Broadcast Operations:**
- Morning planning and daypart window decisions
- EPG/guide listing adjustments
- Proactive viewer communications

**For Traffic Operations:**
- Schedule coordination
- Backup programming preparation

**For Sports Operations:**
- Game impact assessment
- Resource allocation planning

---

## 🌟 System Benefits

- **⏱️ Time Savings:** ~300 hours per season
- **🎯 Risk Reduction:** Never miss weather events
- **📊 Complete Coverage:** All 30 MLB teams, Spring Training + Regular Season
- **🔔 Proactive Alerts:** Know about issues before games start
- **💰 Cost Effective:** $0 annual operating cost

---

## 📈 Status

**Current Season:** 2026 Spring Training → Regular Season  
**Operational Status:** ✅ Fully Automated  
**Last Validated:** March 21, 2026  
**Uptime:** 99.9% (GitHub Actions SLA)

---

## 👤 Maintainer

**Luis Evangelista**  
Sports Operations  
[GitHub: @Sports-Weather2](https://github.com/Sports-Weather2)

---

## 📄 License

Internal tool for broadcast operations use.

---

## 🔗 Quick Links

- [Confluence User Guide](https://confluence.dtveng.net/spaces/~le805s/pages/793701279/)
- [GitHub Repository](https://github.com/Sports-Weather2/mlb-weather-bot)
- Slack: #gameday-weather
- Slack: #high-risk-weather-alert

---

**⚾ Automated. Reliable. Zero Cost.**
