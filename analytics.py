"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🌤️ MLB WEATHER BOT - ANALYTICS TRACKER
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PURPOSE:
Tracks all system activity, alerts sent, prediction accuracy, and workflow
performance. This data helps validate the system's effectiveness and ROI.

WHAT IT TRACKS:
- Total games monitored
- Alerts sent (by type)
- Prediction accuracy (did we correctly predict delays?)
- Workflow reliability (success/failure rates)
- Daily activity patterns

DATA STORAGE:
All data is stored in analytics.json and persists between runs.
Automatically generates ANALYTICS.md for beautiful GitHub display.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import json
import os
from datetime import datetime, timedelta
import pytz

# File where all analytics data is stored
ANALYTICS_FILE = 'analytics.json'

# ============================================
# DATA LOADING & INITIALIZATION
# ============================================

def load_analytics():
    """
    Load analytics data from file
    
    Returns:
        Dictionary containing all analytics data
        
    If file doesn't exist, creates new analytics structure
    """
    try:
        with open(ANALYTICS_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return initialize_analytics()

def initialize_analytics():
    """
    Create a new analytics data structure
    
    Returns:
        Dictionary with empty analytics ready to track data
        
    Called automatically if analytics.json doesn't exist yet
    """
    return {
        "metadata": {
            "created": datetime.now(pytz.timezone('America/Los_Angeles')).isoformat(),
            "last_updated": datetime.now(pytz.timezone('America/Los_Angeles')).isoformat(),
            "season": "Spring Training 2026"
        },
        "totals": {
            # Total number of MLB games we've checked weather for
            "games_monitored": 0,
            
            # Total alerts sent across all types
            "alerts_sent": 0,
            
            # Breakdown by alert type:
            "daily_reports_sent": 0,          # 7 AM daily weather reports
            "high_risk_alerts_sent": 0,       # 10 AM high-risk weather alerts
            "delay_alerts_sent": 0,           # Rain delay detected
            "resumption_alerts_sent": 0,      # Game resuming from delay
            "postponement_alerts_sent": 0     # Game postponed/cancelled
        },
        "accuracy": {
            # How many times we predicted a delay correctly
            "delays_predicted": 0,
            
            # How many actual delays occurred (from MLB official data)
            "actual_delays": 0,
            
            # False positives: We predicted delay but game played normally
            "false_positives": 0,
            
            # False negatives: We missed predicting a delay that happened
            "false_negatives": 0
        },
        "workflow_runs": {
            # Total times workflows ran (scheduled + manual)
            "total_runs": 0,
            
            # Successful completions
            "successful_runs": 0,
            
            # Failed runs (errors, API issues, etc.)
            "failed_runs": 0,
            
            # Skipped runs (time check failed - not 7 AM or 10 AM)
            "skipped_runs": 0
        },
        "daily_activity": {
            # Date-by-date breakdown of activity
            # Format: "2026-03-21": { alerts_sent: X, games_monitored: Y, ... }
        }
    }

def save_analytics(analytics):
    """
    Save analytics data and update markdown display
    
    Args:
        analytics: Dictionary containing all analytics data
        
    Automatically updates:
    1. analytics.json (raw data)
    2. ANALYTICS.md (formatted display for GitHub)
    """
    analytics['metadata']['last_updated'] = datetime.now(pytz.timezone('America/Los_Angeles')).isoformat()
    
    # Save JSON data
    with open(ANALYTICS_FILE, 'w') as f:
        json.dump(analytics, f, indent=2)
    
    # Update markdown display
    generate_analytics_markdown()

# ============================================
# TRACKING FUNCTIONS
# ============================================

def log_alert(alert_type):
    """
    Record that an alert was sent to Slack
    
    Args:
        alert_type: Type of alert sent
            - 'daily_report': 7 AM daily weather report
            - 'high_risk': 10 AM high-risk weather alert
            - 'delay': Rain delay detected
            - 'resumption': Game resuming from delay
            - 'postponement': Game postponed/cancelled
            
    This function:
    1. Increments the total alert counter
    2. Increments the specific alert type counter
    3. Records the timestamp in daily activity log
    4. Saves everything to analytics.json
    """
    analytics = load_analytics()
    pacific_tz = pytz.timezone('America/Los_Angeles')
    today = datetime.now(pacific_tz).strftime('%Y-%m-%d')
    
    # Update total alerts sent
    analytics['totals']['alerts_sent'] += 1
    
    # Update specific alert type counter
    if alert_type == 'daily_report':
        analytics['totals']['daily_reports_sent'] += 1
    elif alert_type == 'high_risk':
        analytics['totals']['high_risk_alerts_sent'] += 1
    elif alert_type == 'delay':
        analytics['totals']['delay_alerts_sent'] += 1
    elif alert_type == 'resumption':
        analytics['totals']['resumption_alerts_sent'] += 1
    elif alert_type == 'postponement':
        analytics['totals']['postponement_alerts_sent'] += 1
    
    # Record in daily activity log
    if today not in analytics['daily_activity']:
        analytics['daily_activity'][today] = {
            'alerts_sent': 0,
            'games_monitored': 0,
            'alert_types': []
        }
    
    analytics['daily_activity'][today]['alerts_sent'] += 1
    analytics['daily_activity'][today]['alert_types'].append({
        'type': alert_type,
        'timestamp': datetime.now(pacific_tz).isoformat()
    })
    
    save_analytics(analytics)
    print(f"📊 Logged {alert_type} alert to analytics")

def log_games_monitored(game_count):
    """
    Record how many MLB games were checked for weather
    
    Args:
        game_count: Number of games monitored in this run
        
    Called by the daily weather report to track total games monitored
    """
    analytics = load_analytics()
    pacific_tz = pytz.timezone('America/Los_Angeles')
    today = datetime.now(pacific_tz).strftime('%Y-%m-%d')
    
    # Add to total games monitored
    analytics['totals']['games_monitored'] += game_count
    
    # Record in daily activity
    if today not in analytics['daily_activity']:
        analytics['daily_activity'][today] = {
            'alerts_sent': 0,
            'games_monitored': 0,
            'alert_types': []
        }
    
    analytics['daily_activity'][today]['games_monitored'] += game_count
    
    save_analytics(analytics)
    print(f"📊 Logged {game_count} games monitored")

def log_workflow_run(status):
    """
    Record that a GitHub Actions workflow ran
    
    Args:
        status: Result of the workflow run
            - 'success': Workflow completed successfully
            - 'failed': Workflow encountered an error
            - 'skipped': Time check failed (not 7 AM or 10 AM)
            
    Helps track system reliability and uptime
    """
    analytics = load_analytics()
    
    # Increment total runs
    analytics['workflow_runs']['total_runs'] += 1
    
    # Increment specific status counter
    if status == 'success':
        analytics['workflow_runs']['successful_runs'] += 1
    elif status == 'failed':
        analytics['workflow_runs']['failed_runs'] += 1
    elif status == 'skipped':
        analytics['workflow_runs']['skipped_runs'] += 1
    
    save_analytics(analytics)
    print(f"📊 Logged workflow run: {status}")

def log_prediction_accuracy(predicted_delay, actual_delay):
    """
    Track how accurate our weather predictions are
    
    Args:
        predicted_delay: Boolean - Did we predict a delay? (>70% rain or thunderstorms)
        actual_delay: Boolean - Did MLB actually delay the game?
        
    This helps validate the system's effectiveness:
    - True Positive: We predicted delay AND it happened ✅
    - False Positive: We predicted delay but game played normally ❌
    - False Negative: We didn't predict delay but it happened ❌
    - True Negative: We said clear and game played (not tracked - too many)
    """
    analytics = load_analytics()
    
    if predicted_delay and actual_delay:
        # ✅ TRUE POSITIVE - We predicted correctly!
        analytics['accuracy']['delays_predicted'] += 1
        analytics['accuracy']['actual_delays'] += 1
    elif predicted_delay and not actual_delay:
        # ❌ FALSE POSITIVE - We cried wolf (predicted delay but game was fine)
        analytics['accuracy']['false_positives'] += 1
    elif not predicted_delay and actual_delay:
        # ❌ FALSE NEGATIVE - We missed it (didn't predict but delay happened)
        analytics['accuracy']['false_negatives'] += 1
        analytics['accuracy']['actual_delays'] += 1
    # True negatives (predicted clear, game was clear) are not tracked
    # because there would be too many and they're less interesting
    
    save_analytics(analytics)

# ============================================
# REPORTING FUNCTIONS
# ============================================

def generate_summary_report():
    """
    Generate a comprehensive analytics summary report
    
    Returns:
        Formatted string with all analytics data
        
    Perfect for:
    - Leadership presentations
    - Validating system effectiveness
    - Proving ROI (time saved, accuracy, reliability)
    """
    analytics = load_analytics()
    
    # Calculate prediction accuracy percentage
    total_delays = analytics['accuracy']['actual_delays']
    correct_predictions = analytics['accuracy']['delays_predicted']
    
    if total_delays > 0:
        accuracy_pct = (correct_predictions / total_delays) * 100
    else:
        accuracy_pct = 0
    
    # Calculate workflow success rate
    total_runs = analytics['workflow_runs']['total_runs']
    successful_runs = analytics['workflow_runs']['successful_runs']
    
    if total_runs > 0:
        success_rate = (successful_runs / total_runs) * 100
    else:
        success_rate = 0
    
    # Build the formatted report
    report = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 MLB WEATHER BOT - ANALYTICS SUMMARY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Season: {analytics['metadata']['season']}
Report Generated: {datetime.now(pytz.timezone('America/Los_Angeles')).strftime('%Y-%m-%d %I:%M %p PT')}

OVERALL STATISTICS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Games Monitored:           {analytics['totals']['games_monitored']}
Total Alerts Sent:         {analytics['totals']['alerts_sent']}

ALERT BREAKDOWN
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 Daily Reports:          {analytics['totals']['daily_reports_sent']}
🚨 High-Risk Alerts:       {analytics['totals']['high_risk_alerts_sent']}
⏸️  Delay Alerts:          {analytics['totals']['delay_alerts_sent']}
▶️  Resumption Alerts:     {analytics['totals']['resumption_alerts_sent']}
📅 Postponement Alerts:    {analytics['totals']['postponement_alerts_sent']}

PREDICTION ACCURACY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Actual Delays:             {analytics['accuracy']['actual_delays']}
Correctly Predicted:       {analytics['accuracy']['delays_predicted']}
Accuracy Rate:             {accuracy_pct:.1f}%
False Positives:           {analytics['accuracy']['false_positives']}
False Negatives:           {analytics['accuracy']['false_negatives']}

SYSTEM RELIABILITY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Total Workflow Runs:       {analytics['workflow_runs']['total_runs']}
Successful:                {analytics['workflow_runs']['successful_runs']}
Failed:                    {analytics['workflow_runs']['failed_runs']}
Skipped (time check):      {analytics['workflow_runs']['skipped_runs']}
Success Rate:              {success_rate:.1f}%

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    """
    
    return report

def generate_analytics_markdown():
    """
    Generate ANALYTICS.md - a formatted markdown file with analytics data
    
    Creates a beautiful display that renders nicely in GitHub
    Similar to STATUS.md format
    """
    analytics = load_analytics()
    pacific_tz = pytz.timezone('America/Los_Angeles')
    now = datetime.now(pacific_tz)
    
    # Calculate accuracy percentage
    total_delays = analytics['accuracy']['actual_delays']
    correct_predictions = analytics['accuracy']['delays_predicted']
    accuracy_pct = (correct_predictions / total_delays * 100) if total_delays > 0 else 0
    
    # Calculate success rate
    total_runs = analytics['workflow_runs']['total_runs']
    successful_runs = analytics['workflow_runs']['successful_runs']
    success_rate = (successful_runs / total_runs * 100) if total_runs > 0 else 0
    
    # Get today and yesterday stats
    today = now.strftime('%Y-%m-%d')
    yesterday = (now - timedelta(days=1)).strftime('%Y-%m-%d')
    
    today_stats = analytics['daily_activity'].get(today, {'alerts_sent': 0, 'games_monitored': 0})
    yesterday_stats = analytics['daily_activity'].get(yesterday, {'alerts_sent': 0, 'games_monitored': 0})
    
    # Estimate time saved (50 minutes saved per active day)
    days_active = len(analytics['daily_activity'])
    time_saved_hours = days_active * 0.83
    
    # Build the markdown content
    markdown = f"""# 📊 System Analytics

**MLB Weather Monitoring System**

---

## 🟢 CURRENT PERFORMANCE

**Status:** Fully Operational  
**Last Updated:** {now.strftime('%B %d, %Y %I:%M %p PT')}  
**Season:** {analytics['metadata']['season']}

---

## 📈 Overall Statistics

| Metric | Count |
|--------|-------|
| 📅 Games Monitored | {analytics['totals']['games_monitored']} |
| 📬 Total Alerts Sent | {analytics['totals']['alerts_sent']} |
| 📊 Daily Reports | {analytics['totals']['daily_reports_sent']} |
| 🚨 High-Risk Alerts | {analytics['totals']['high_risk_alerts_sent']} |
| ⏸️ Delay Alerts | {analytics['totals']['delay_alerts_sent']} |
| ▶️ Resumption Alerts | {analytics['totals']['resumption_alerts_sent']} |
| 📅 Postponement Alerts | {analytics['totals']['postponement_alerts_sent']} |

---

## 🎯 Prediction Accuracy

| Metric | Value |
|--------|-------|
| Actual Delays Occurred | {analytics['accuracy']['actual_delays']} |
| Correctly Predicted | {analytics['accuracy']['delays_predicted']} |
| **Accuracy Rate** | **{accuracy_pct:.1f}%** |
| False Positives | {analytics['accuracy']['false_positives']} |
| False Negatives | {analytics['accuracy']['false_negatives']} |

---

## 🔧 System Reliability

| Metric | Count | Percentage |
|--------|-------|------------|
| Total Workflow Runs | {analytics['workflow_runs']['total_runs']} | - |
| ✅ Successful | {analytics['workflow_runs']['successful_runs']} | {success_rate:.1f}% |
| ❌ Failed | {analytics['workflow_runs']['failed_runs']} | {(analytics['workflow_runs']['failed_runs']/total_runs*100) if total_runs > 0 else 0:.1f}% |
| ⏭️ Skipped (time check) | {analytics['workflow_runs']['skipped_runs']} | {(analytics['workflow_runs']['skipped_runs']/total_runs*100) if total_runs > 0 else 0:.1f}% |

**System Uptime:** {success_rate:.1f}%

---

## 📅 Recent Activity

### Today ({now.strftime('%B %d, %Y')})

- 📊 Alerts sent: {today_stats['alerts_sent']}
- 📅 Games monitored: {today_stats['games_monitored']}

### Yesterday ({(now - timedelta(days=1)).strftime('%B %d, %Y')})

- 📊 Alerts sent: {yesterday_stats['alerts_sent']}
- 📅 Games monitored: {yesterday_stats['games_monitored']}

---

## 💡 Key Insights

**Time Saved:** ~{time_saved_hours:.0f} hours this season  
**Estimated Value:** ${time_saved_hours * 50:.0f} in operational efficiency

**Days Active:** {days_active}  
**Average Alerts/Day:** {analytics['totals']['alerts_sent'] / days_active if days_active > 0 else 0:.1f}

---

## 🔄 Data Updates

This file is automatically updated by `analytics.py` after each workflow run.

**Update Frequency:** Real-time (after each alert sent)

---

_Last generated: {now.strftime('%B %d, %Y %I:%M %p PT')}_
"""
    
    # Write to ANALYTICS.md file
    with open('ANALYTICS.md', 'w') as f:
        f.write(markdown)
    
    print("📊 Updated ANALYTICS.md")

def get_daily_stats(date=None):
    """
    Get statistics for a specific date
    
    Args:
        date: Date string in format 'YYYY-MM-DD' (defaults to today)
        
    Returns:
        Dictionary with that day's statistics, or None if no data
        
    Useful for checking:
    - Did the system run today?
    - How many alerts were sent?
    - What games were monitored?
    """
    analytics = load_analytics()
    
    if date is None:
        date = datetime.now(pytz.timezone('America/Los_Angeles')).strftime('%Y-%m-%d')
    
    if date in analytics['daily_activity']:
        return analytics['daily_activity'][date]
    else:
        return None

# ============================================
# TESTING / EXAMPLE USAGE
# ============================================

if __name__ == "__main__":
    """
    When you run this file directly (python analytics.py),
    it prints the current analytics summary report and updates ANALYTICS.md.
    
    Useful for:
    - Checking system performance
    - Generating reports for leadership
    - Validating data is being tracked correctly
    """
    print(generate_summary_report())
    generate_analytics_markdown()
    print("\n✅ ANALYTICS.md has been updated!")
