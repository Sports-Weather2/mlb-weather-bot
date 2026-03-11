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
    },
    'monitor': {
        'rain_prob': 40,
        'wind_sustained': 15,
        'temp_concern': [40, 95]
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
    
    closest_forecast = min(forecasts, 
                          key=lambda x: abs(x['dt'] - game_timestamp))
    
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

def calculate_game_impact(weather):
    if (weather['rain_prob'] >= IMPACT_RULES['high_risk']['rain_prob'] or
        weather['wind_gust'] >= IMPACT_RULES['high_risk']['wind_gust'] or
        weather['has_thunderstorm'] or
        weather['temp'] <= IMPACT_RULES['high_risk']['temp_extreme'][0] or
        weather['temp'] >= IMPACT_RULES['high_risk']['temp_extreme'][1]):
        
        return {
            'level': 'HIGH_RISK',
            'emoji': '🔴',
            'status': 'HIGH RISK',
            'color': '#dc3545'
        }
    
    elif (weather['rain_prob'] >= IMPACT_RULES['monitor']['rain_prob'] or
          weather['wind_speed'] >= IMPACT_RULES['monitor']['wind_sustained'] or
          weather['temp'] <= IMPACT_RULES['monitor']['temp_concern'][0] or
          weather['temp'] >= IMPACT_RULES['monitor']['temp_concern'][1]):
        
        return {
            'level': 'MONITOR',
            'emoji': '🟡',
            'status': 'MONITOR',
            'color': '#ffc107'
        }
    
    else:
        return {
            'level': 'CLEAR',
            'emoji': '🟢',
            'status': 'CLEAR',
            'color': '#28a745'
        }

def format_game_block(game, weather, impact):
    game_datetime = datetime.strptime(
        f"{game['date']} {game['time']}", 
        "%Y-%m-%d %H:%M"
    )
    
    date_str = game_datetime.strftime("%A, %B %d")
    time_str = game_datetime.strftime("%I:%M %p")
    
    weather_details = (
        f"🌡️ *{weather['temp']:.0f}°F* (feels like {weather['feels_like']:.0f}°F)\n"
        f"☁️ {weather['conditions'].title()}\n"
        f"💧 Rain: *{weather['rain_prob']:.0f}%*\n"
        f"💨 Wind: {weather['wind_speed']:.0f} mph"
    )
    
    if weather['wind_gust'] > weather['wind_speed'] + 5:
        weather_details += f" (gusts to {weather['wind_gust']:.0f} mph)"
    
    blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*⚾ {game['opponent']}*\n{date_str} at {time_str}"
            }
        },
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": f"*Weather Forecast:*\n{weather_details}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Game Impact:*\n{impact['emoji']} *{impact['status']}*"
                }
            ]
        }
    ]
    
    if impact['level'] == 'HIGH_RISK':
        blocks.insert(0, {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "⚠️ *WEATHER ALERT* - High risk of game impact"
            }
        })
    
    return blocks

def build_slack_message(games_weather):
    # Get current time in Pacific timezone
    pacific_tz = pytz.timezone('America/Los_Angeles')
    now = datetime.now(pacific_tz)
    
    high_risk_count = sum(1 for g in games_weather if g['impact']['level'] == 'HIGH_RISK')
    monitor_count = sum(1 for g in games_weather if g['impact']['level'] == 'MONITOR')
    
    if high_risk_count > 0:
        header_emoji = "🚨"
        summary = f"{high_risk_count} game(s) at HIGH RISK"
    elif monitor_count > 0:
        header_emoji = "⚠️"
        summary = f"{monitor_count} game(s) to MONITOR"
    else:
        header_emoji = "✅"
        summary = "All games clear"
    
    message = {
        "text": f"Weather Update: {summary}",
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{header_emoji} Game Day Weather Impact Report",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{summary}* | Next 24 Hours"
                }
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"Updated: {now.strftime('%b %d at %I:%M %p')} PT | Next update: 7:00 AM PT tomorrow"
                    }
                ]
            },
            {
                "type": "divider"
            }
        ]
    }
    
    for game_data in games_weather:
        game_blocks = format_game_block(
            game_data['game'],
            game_data['weather'],
            game_data['impact']
        )
        
        message["blocks"].extend(game_blocks)
        message["blocks"].append({"type": "divider"})
    
    message["blocks"].extend([
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": "🟢 *CLEAR* - No concerns | 🟡 *MONITOR* - Prepare for possible issues | 🔴 *HIGH RISK* - Significant weather threat"
                }
            ]
        }
    ])
    
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
    upcoming_games = []
    
    print(f"🔍 Checking weather for games...")
    
    for game in games:
        game_datetime = datetime.strptime(
            f"{game['date']} {game['time']}", 
            "%Y-%m-%d %H:%M"
        )
        
        if now.replace(tzinfo=None) <= game_datetime <= now.replace(tzinfo=None) + timedelta(hours=48):
            print(f"  📅 {game['opponent']} - {game['date']} {game['time']}")
            
            weather = get_weather_forecast(game['location'], game_datetime)
            impact = calculate_game_impact(weather)
            
            upcoming_games.append({
                'game': game,
                'weather': weather,
                'impact': impact
            })
            
            print(f"     {impact['emoji']} {impact['status']}")
    
    if not upcoming_games:
        print("ℹ️  No games in next 48 hours - skipping update")
        return
    
    # Sort games by risk level: HIGH_RISK first, MONITOR second, CLEAR last
    risk_priority = {'HIGH_RISK': 0, 'MONITOR': 1, 'CLEAR': 2}
    upcoming_games.sort(key=lambda x: risk_priority[x['impact']['level']])
    
    print(f"\n📊 Games sorted by risk level (HIGH_RISK → MONITOR → CLEAR)")
    
    # Limit to 10 games to stay under Slack's 50-block limit
    if len(upcoming_games) > 10:
        print(f"⚠️ Limiting to top 10 games (total available: {len(upcoming_games)})")
        upcoming_games = upcoming_games[:10]
    
    message = build_slack_message(upcoming_games)
    
    if post_to_slack(message):
        print(f"\n✅ Weather impact report posted for {len(upcoming_games)} game(s)")
        
        high_risk = sum(1 for g in upcoming_games if g['impact']['level'] == 'HIGH_RISK')
        monitor = sum(1 for g in upcoming_games if g['impact']['level'] == 'MONITOR')
        clear = sum(1 for g in upcoming_games if g['impact']['level'] == 'CLEAR')
        
        print(f"   🔴 High Risk: {high_risk}")
        print(f"   🟡 Monitor: {monitor}")
        print(f"   🟢 Clear: {clear}")
    else:
        print("❌ Failed to post to Slack")

if __name__ == "__main__":
    main()
