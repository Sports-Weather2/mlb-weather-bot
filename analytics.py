import json
import os
from datetime import datetime, timedelta
import pytz

ANALYTICS_FILE = 'analytics.json'

def load_analytics():
    """Load analytics data"""
    try:
        with open(ANALYTICS_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return initialize_analytics()

def initialize_analytics():
    """Initialize analytics structure"""
    return {
        "metadata": {
            "created": datetime.now(pytz.timezone('America/Los_Angeles')).isoformat(),
            "last_updated": datetime.now(pytz.timezone('America/Los_Angeles')).isoformat(),
            "season": "Spring Training 2026"
        },
        "totals": {
            "games_monitored": 0,
            "alerts_sent": 0,
            "daily_reports_sent": 0,
            "high_risk_alerts_sent": 0,
            "delay_alerts_sent": 0,
            "resumption_alerts_sent": 0,
            "postponement_alerts_sent": 0
        },
        "accuracy": {
            "delays_predicted": 0,
            "actual_delays": 0,
            "false_positives": 0,
            "false_negatives": 0
        },
        "workflow_runs": {
            "total_runs": 0,
            "successful_runs": 0,
            "failed_runs": 0,
            "skipped_runs": 0
        },
        "daily_activity": {}
    }

def save_analytics(analytics):
    """Save analytics data"""
    analytics['metadata']['last_updated'] = datetime.now(pytz.timezone('America/Los_Angeles')).isoformat()
    with open(ANALYTICS_FILE, 'w') as f:
        json.dump(analytics, f, indent=2)

def log_alert(alert_type):
    """
    Log an alert being sent
    
    Args:
        alert_type: 'daily_report', 'high_risk', 'delay', 'resumption', 'postponement'
    """
    analytics = load_analytics()
    pacific_tz = pytz.timezone('America/Los_Angeles')
    today = datetime.now(pacific_tz).strftime('%Y-%m-%d')
    
    # Update totals
    analytics['totals']['alerts_sent'] += 1
    
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
    
    # Update daily activity
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
    """Log number of games monitored"""
    analytics = load_analytics()
    pacific_tz = pytz.timezone('America/Los_Angeles')
    today = datetime.now(pacific_tz).strftime('%Y-%m-%d')
    
    analytics['totals']['games_monitored'] += game_count
    
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
    Log a workflow run
    
    Args:
        status: 'success', 'failed', or 'skipped'
    """
    analytics = load_analytics()
    
    analytics['workflow_runs']['total_runs'] += 1
    
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
    Track prediction accuracy
    
    Args:
        predicted_delay: Boolean - did we predict a delay?
        actual_delay: Boolean - did a delay actually occur?
    """
    analytics = load_analytics()
    
    if predicted_delay and actual_delay:
        # True positive - we predicted correctly
        analytics['accuracy']['delays_predicted'] += 1
        analytics['accuracy']['actual_delays'] += 1
    elif predicted_delay and not actual_delay:
        # False positive - we predicted but no delay
        analytics['accuracy']['false_positives'] += 1
    elif not predicted_delay and actual_delay:
        # False negative - we missed a delay
        analytics['accuracy']['false_negatives'] += 1
        analytics['accuracy']['actual_delays'] += 1
    
    save_analytics(analytics)

def generate_summary_report():
    """Generate a summary report of analytics"""
    analytics = load_analytics()
    
    # Calculate accuracy percentage
    total_delays = analytics['accuracy']['actual_delays']
    correct_predictions = analytics['accuracy']['delays_predicted']
    
    if total_delays > 0:
        accuracy_pct = (correct_predictions / total_delays) * 100
    else:
        accuracy_pct = 0
    
    # Calculate success rate
    total_runs = analytics['workflow_runs']['total_runs']
    successful_runs = analytics['workflow_runs']['successful_runs']
    
    if total_runs > 0:
        success_rate = (successful_runs / total_runs) * 100
    else:
        success_rate = 0
    
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

def get_daily_stats(date=None):
    """Get statistics for a specific date"""
    analytics = load_analytics()
    
    if date is None:
        date = datetime.now(pytz.timezone('America/Los_Angeles')).strftime('%Y-%m-%d')
    
    if date in analytics['daily_activity']:
        return analytics['daily_activity'][date]
    else:
        return None

# Example usage
if __name__ == "__main__":
    # Print current analytics
    print(generate_summary_report())
