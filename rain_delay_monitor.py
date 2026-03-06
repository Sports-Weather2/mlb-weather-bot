import os
import json
import requests
from datetime import datetime, timedelta

SLACK_WEBHOOK = os.environ.get('SLACK_WEBHOOK')

def load_games():
    """Load game schedule"""
    with open('config.json', 'r') as f:
        return json.load(f)['games']

def get_games_in_progress():
    """Get games that should be happening now or soon"""
    games = load_games()
    now = datetime.now()
    in_progress = []
    
    for game in games:
        game_datetime = datetime.strptime(f"{game['date']} {game['time']}", "%Y-%m-%d %H:%M")
        
        # Check if game is within 30 min before start to 4 hours after start
        time_before = game_datetime - timedelta(minutes=30)
        time_after = game_datetime + timedelta(hours=4)
        
        if time_before <= now <= time_after:
            in_progress.append(game)
    
    return in_progress

def check_mlb_game_status():
    """
    Check if there are any weather-related delays
    Note: This is a simplified version. In production, you'd integrate with MLB's API
    or scraping real-time game status.
    """
    games = get_games_in_progress()
    
    if not games:
        print("No games currently in progress")
        return
    
    for game in games:
        # Check for severe weather at game location
        weather = get_current_weather(game['location'])
        
        if is_game_threatening_weather(weather):
            send_delay_alert(game, weather)

def get_current_weather(location):
    """Get current weather conditions"""
    WEATHER_API_KEY = os.environ.get('WEATHER_API_KEY')
    url = f"https://api.openweathermap.org/data/2.5/weather?q={location}&appid={WEATHER_API_KEY}&units=imperial"
    
    response = requests.get(url)
    data = response.json()
    
    weather_id = data['weather'][0]['id']
    
    return {
        'temp': data['main']['temp'],
        'conditions': data['weather'][0]['description'],
        'rain': data.get('rain', {}).get('1h', 0),
        'wind_speed': data['wind']['speed'],
        'has_thunderstorm': 200 <= weather_id < 300,
        'has_rain': 500 <= weather_id < 600
    }

def is_game_threatening_weather(weather):
    """Determine if weather is threatening to game"""
    if weather['has_thunderstorm']:
        return True
    if weather['rain'] > 0.1:  # More than 0.1 inches per hour
        return True
    return False

def send_delay_alert(game, weather):
    """Send urgent Slack alert"""
    message = {
        "text": "⚠️ WEATHER DELAY RISK",
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "🚨 URGENT: Weather Delay Risk",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*⚾ {game['opponent']}*\nGame in progress or starting soon"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Location:*\n{game['location']}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Current Weather:*\n{weather['conditions']}"
                    }
                ]
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*⚠️ Alert Reason:*"
                }
            }
        ]
    }
    
    # Add specific alerts
    alerts = []
    if weather['has_thunderstorm']:
        alerts.append("• ⚡ Thunderstorm detected - Lightning delay likely")
    if weather['rain'] > 0.1:
        alerts.append(f"• 🌧️ Heavy rain detected ({weather['rain']:.2f} in/hr)")
    
    alert_text = "\n".join(alerts)
    message["blocks"].append({
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": alert_text
        }
    })
    
    message["blocks"].append({
        "type": "context",
        "elements": [
            {
                "type": "mrkdwn",
                "text": f"<!channel> Immediate attention needed for scheduling | {datetime.now().strftime('%I:%M %p')}"
            }
        ]
    })
    
    response = requests.post(SLACK_WEBHOOK, json=message)
    
    if response.status_code == 200:
        print(f"🚨 Delay alert sent for: {game['opponent']}")
    else:
        print(f"Failed to send alert: {response.status_code}")

def main():
    """Main monitoring loop"""
    print(f"🔍 Checking for games in progress at {datetime.now().strftime('%I:%M %p')}")
    check_mlb_game_status()

if __name__ == "__main__":
    main()
