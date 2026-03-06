import os
import json
import requests
from datetime import datetime, timedelta

SLACK_WEBHOOK = os.environ.get('SLACK_WEBHOOK')
WEATHER_API_KEY = os.environ.get('WEATHER_API_KEY')
ALERT_MODE = os.environ.get('ALERT_MODE', 'monitor')  # 'daily' or 'monitor'
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

def build_daily_report(all_games_data):
    """Build morning daily report - shows all games with risk levels"""
    now = datetime.now()
    high_risk = [g for g in all_games_data if g['is_high_risk']]
    normal = [g for g in all_games_data if not g['is_high_risk']]
    
    message = {
        "text": f"☀️ Morning Weather Report: {len(all_games_data)} games in next 48hrs",
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "☀️ Daily Weather Report",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Games in next 48 hours:* {len(all_games_data)}\n🔴 High Risk: {len(high_risk)} | ✅ Normal: {len(normal)}"
                }
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"Daily Report | {now.strftime('%A, %B %d at %I:%M %p')} | Next monitoring checks every 15 min during game hours"
                    }
                ]
            },
            {
                "type": "divider"
            }
        ]
    }
    
    # Add high-risk games first
    if high_risk:
        message["blocks"].append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*🔴 HIGH RISK GAMES*"
            }
        })
        
        for game_data in high_risk:
            game = game_data['game']
            weather = game_data['weather']
            
            game_datetime = datetime.strptime(f"{game['date']} {game['time']}", "%Y-%m-%d %H:%M")
            date_str = game_datetime.strftime("%a %b %d")
            time_str = game_datetime.strftime("%I:%M %p")
            
            weather_details = f"🌡️ {weather['temp']:.0f}°F | "
            weather_details += f"💧 {weather['rain_prob']:.0f}% rain | "
            weather_details += f"💨 {weather['wind_speed']:.0f} mph"
            
            if weather['wind_gust'] > weather['wind_speed'] + 5:
                weather_details += f" (gusts {weather['wind_gust']:.0f})"
            
            if weather['has_thunderstorm']:
                weather_details += " | ⚡ T-storms"
            
            message["blocks"].append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{game['opponent']}* - {date_str} at {time_str}\n{weather_details}"
                }
            })
    
    # Add normal games
    if normal:
        message["blocks"].append({"type": "divider"})
        message["blocks"].append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*✅ NORMAL CONDITIONS*"
            }
        })
        
        for game_data in normal:
            game = game_data['game']
            weather = game_data['weather']
            
            game_datetime = datetime.strptime(f"{game['date']} {game['time']}", "%Y-%m-%d %H:%M")
            date_str = game_datetime.strftime("%a %b %d")
            time_str = game_datetime.strftime("%I:%M %p")
            
            weather_details = f"🌡️ {weather['temp']:.0f}°F | 💧 {weather['rain_prob']:.0f}% | 💨 {weather['wind_speed']:.0f} mph"
            
            message["blocks"].append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{game['opponent']}* - {date_str} at {time_str}\n{weather_details}"
                }
            })
    
    if not all_games_data:
        message["blocks"].append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "_No games scheduled in the next 48 hours_"
            }
        })
    
    return message

def build_live_alert(high_risk_games):
    """Build live monitoring alert - only for high-risk games"""
    now = datetime.now()
    
    message = {
        "text": f"🚨 LIVE ALERT: {len(high_risk_games)} HIGH RISK game(s)",
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
                    "text": f"*{len(high_risk_games)} game(s)* now at HIGH RISK - immediate attention needed"
                }
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"Live Monitor | {now.strftime('%I:%M %p')} | Next check in 15 minutes"
                    }
                ]
            },
            {
                "type": "divider"
            }
        ]
    }
    
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
        
        message["blocks"].append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*🔴 {game['opponent']}*\n{date_str} at {time_str}\n{weather_details}"
            }
        })
        message["blocks"].append({"type": "divider"})
    
    message["blocks"].append({
        "type": "context",
        "elements": [
            {
                "type": "mrkdwn",
                "text": "🔴 *HIGH RISK* = >70% rain OR thunderstorms OR extreme temps OR high winds (>30mph)"
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
    now = datetime.now()
    all_games_data = []
    high_risk_games = []
    
    print(f"🔍 Mode: {ALERT_MODE.upper()}")
    print(f"🔍 Checking weather for games in next 48 hours...")
    
    for game in games:
        game_datetime = datetime.strptime(f"{game['date']} {game['time']}", "%Y-%m-%d %H:%M")
        
        # Check games within next 48 hours
        if now <= game_datetime <= now + timedelta(hours=48):
            weather = get_weather_forecast(game['location'], game_datetime)
            is_risk = is_high_risk(weather)
            
            game_data = {
                'game': game,
                'weather': weather,
                'is_high_risk': is_risk
            }
            
            all_games_data.append(game_data)
            
            if is_risk:
                high_risk_games.append(game_data)
                print(f"  🔴 HIGH RISK: {game['opponent']} - {game['date']} {game['time']}")
            else:
                print(f"  ✅ Normal: {game['opponent']} - {game['date']} {game['time']}")
    
    print(f"\n📊 Total games: {len(all_games_data)} | High-risk: {len(high_risk_games)}")
    
    # Decide what to post based on mode
    if ALERT_MODE == 'daily':
        # Morning report - always post full summary
        print("📬 Posting daily morning report...")
        message = build_daily_report(all_games_data)
        if post_to_slack(message):
            print(f"✅ Daily report posted ({len(all_games_data)} games)")
        else:
            print("❌ Failed to post daily report")
    
    else:  # monitor mode
        # Live monitoring - only post if high-risk
        if high_risk_games:
            print("🚨 High-risk weather detected - posting alert...")
            message = build_live_alert(high_risk_games)
            if post_to_slack(message):
                print(f"✅ Live alert posted for {len(high_risk_games)} game(s)")
            else:
                print("❌ Failed to post live alert")
        else:
            print("✅ No high-risk weather - silent check (no alert needed)")

if __name__ == "__main__":
    main()
