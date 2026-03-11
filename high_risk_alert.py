import os
import json
import requests
import pytz
from datetime import datetime, timedelta

SLACK_WEBHOOK = os.environ.get('SLACK_WEBHOOK')
WEATHER_API_KEY = os.environ.get('WEATHER_API_KEY')
WEATHER_BASE_URL = "https://api.openweathermap.org/data/2.5/forecast"

IMPACT_RULES = {
    'high_risk': {
        'rain_prob': 70,
        'wind_gust': 30,
        'lightning': True,
        'temp_extreme': [35, 100]
    }
}

def load_games():
    with open('config.json', 'r') as f:
        return json.load(f)['games']

def get_weather_forecast(location, game_datetime):
    params = {
        'q': location,
        'appid': WEATHER_API_KEY,
        'units': 'imperial'
    }
    
    response = requests.get(WEATHER_BASE_URL, params=params)
    data = response.json()
    
    forecasts = data['list']
    game_timestamp = int(game_datetime.timestamp())
    
    closest_forecast = min(forecasts, key=lambda x: abs(x['dt'] - game_timestamp))
    
    weather_id = closest_forecast['weather'][0]['id']
    has_thunderstorm = 200 <= weather_id < 300
    
    return {
        'temp': closest_forecast['main']['temp'],
        'feels_like': closest_forecast['main']['feels_like'],
        'rain_prob': closest_forecast.get('pop', 0) * 100,
        'conditions': closest_forecast['weather'][0]['description'],
        'wind_speed': closest_forecast['wind']['speed'],
        'wind_gust': closest_forecast['wind'].get('gust', closest_forecast['wind']['speed']),
        'humidity': closest_forecast['main']['humidity'],
        'has_thunderstorm': has_thunderstorm
    }

def is_high_risk(weather):
    """Determine if weather is high risk"""
    if (weather['rain_prob'] >= IMPACT_RULES['high_risk']['rain_prob'] or
        weather['wind_gust'] >= IMPACT_RULES['high_risk']['wind_gust'] or
        weather['has_thunderstorm'] or
        weather['temp'] <= IMPACT_RULES['high_risk']['temp_extreme'][0] or
        weather['temp'] >= IMPACT_RULES['high_risk']['temp_extreme'][1]):
        return True
    return False

def build_high_risk_message(high_risk_games):
    """Build Slack message for high-risk games only"""
    # Get current time in Pacific timezone
    pacific_tz = pytz.timezone('America/Los_Angeles')
    now = datetime.now(pacific_tz)
    
    if not high_risk_games:
        # No high-risk games - send all clear message
        return {
            "text": "✅ No high-risk weather games",
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "✅ All Clear - No High-Risk Weather Games",
                        "emoji": True
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "No games currently at high risk due to weather."
                    }
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": f"Checked at {now.strftime('%I:%M %p')} PT | Next check: {(now + timedelta(hours=3)).strftime('%I:%M %p')} PT"
                        }
                    ]
                }
            ]
        }
    
    # High-risk games exist - build alert
    message = {
        "text": f"🚨 {len(high_risk_games)} HIGH RISK weather game(s)",
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "🚨 HIGH RISK WEATHER ALERT",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{len(high_risk_games)} game(s) at HIGH RISK* requiring attention for daypart/guide adjustments"
                }
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"Updated: {now.strftime('%I:%M %p')} PT | Next check: {(now + timedelta(hours=3)).strftime('%I:%M %p')} PT"
                    }
                ]
            },
            {
                "type": "divider"
            }
        ]
    }
    
    # Add each high-risk game
    for game_data in high_risk_games:
        game = game_data['game']
        weather = game_data['weather']
        
        game_datetime = datetime.strptime(f"{game['date']} {game['time']}", "%Y-%m-%d %H:%M")
        date_str = game_datetime.strftime("%A, %B %d")
        time_str = game_datetime.strftime("%I:%M %p")
        
        weather_details = f"🌡️ {weather['temp']:.0f}°F | "
        weather_details += f"💧 Rain: *{weather['rain_prob']:.0f}%* | "
        weather_details += f"💨 Wind: {weather['wind_speed']:.0f} mph"
        
        if weather['wind_gust'] > weather['wind_speed'] + 5:
            weather_details += f" (gusts {weather['wind_gust']:.0f} mph)"
        
        if weather['has_thunderstorm']:
            weather_details += " | ⚡ *Thunderstorms*"
        
        game_block = {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*🔴 {game['opponent']}*\n{date_str} at {time_str}\n{weather_details}"
            }
        }
        
        message["blocks"].append(game_block)
        message["blocks"].append({"type": "divider"})
    
    # Add footer with legend
    message["blocks"].append({
        "type": "context",
        "elements": [
            {
                "type": "mrkdwn",
                "text": "🔴 *HIGH RISK* = >70% rain OR thunderstorms OR extreme temps OR high winds"
            }
        ]
    })
    
    return message

def post_to_slack(message):
    response = requests.post(
        SLACK_WEBHOOK,
        json=message,
        headers={'Content-Type': 'application/json'}
    )
    
    if response.status_code != 200:
        raise ValueError(f"Slack request failed: {response.status_code}, {response.text}")
    
    return response.status_code == 200

def main():
    games = load_games()
    pacific_tz = pytz.timezone('America/Los_Angeles')
    now = datetime.now(pacific_tz)
    high_risk_games = []
    
    print(f"🔍 Checking for high-risk weather games...")
    
    for game in games:
        game_datetime = datetime.strptime(f"{game['date']} {game['time']}", "%Y-%m-%d %H:%M")
        
        # Check games within next 48 hours
        if now.replace(tzinfo=None) <= game_datetime <= now.replace(tzinfo=None) + timedelta(hours=48):
            weather = get_weather_forecast(game['location'], game_datetime)
            
            if is_high_risk(weather):
                high_risk_games.append({
                    'game': game,
                    'weather': weather
                })
                print(f"  🔴 HIGH RISK: {game['opponent']} - {game['date']} {game['time']}")
    
    print(f"\n📊 Found {len(high_risk_games)} high-risk game(s)")
    
    # Always build and post message (either alerts or all-clear)
    message = build_high_risk_message(high_risk_games)
    
    if post_to_slack(message):
        if high_risk_games:
            print(f"✅ High-risk alert posted for {len(high_risk_games)} game(s)")
        else:
            print("✅ All-clear message posted")
    else:
        print("❌ Failed to post to Slack")

if __name__ == "__main__":
    main()
