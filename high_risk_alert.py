import os
import json
import requests
import pytz
from datetime import datetime, timedelta
from analytics import log_alert, log_workflow_run

SLACK_WEBHOOK = os.environ.get('SLACK_WEBHOOK')
WEATHER_API_KEY = os.environ.get('WEATHER_API_KEY')
WEATHER_BASE_URL = "https://api.openweathermap.org/data/2.5/forecast"

IMPACT_RULES = {
    'high_risk': {
        'rain_prob': 70,
        'wind_gust': 30,
        'lightning': True,
        'temp_extreme': [20, 100]
    }
}

def load_games():
    with open('config.json', 'r') as f:
        return json.load(f)['games']

def get_venue_name_from_location(location):
    """Map location string to official venue name for roof lookup"""
    location_to_venue = {
        # Roofed stadiums
        'Phoenix,US': 'Chase Field',
        'Miami,US': 'loanDepot park',
        'Arlington,US': 'Globe Life Field',
        'Houston,US': 'Minute Maid Park',
        'Seattle,US': 'T-Mobile Park',
        'Milwaukee,US': 'American Family Field',
        'St Petersburg,US': 'Tropicana Field',
        'Toronto,CA': 'Rogers Centre',
        
        # Open-air stadiums (for reference)
        'Anaheim,US': 'Angel Stadium',
        'Los Angeles,US': 'Dodger Stadium',
        'San Francisco,US': 'Oracle Park',
        'San Diego,US': 'Petco Park',
        'Denver,US': 'Coors Field',
        'Kansas City,US': 'Kauffman Stadium',
        'Minneapolis,US': 'Target Field',
        'Chicago,US': 'Guaranteed Rate Field',
        'Cleveland,US': 'Progressive Field',
        'Detroit,US': 'Comerica Park',
        'Cincinnati,US': 'Great American Ball Park',
        'St Louis,US': 'Busch Stadium',
        'Pittsburgh,US': 'PNC Park',
        'New York,US': 'Yankee Stadium',
        'Philadelphia,US': 'Citizens Bank Park',
        'Washington,US': 'Nationals Park',
        'Boston,US': 'Fenway Park',
        'Baltimore,US': 'Oriole Park at Camden Yards',
        'Atlanta,US': 'Truist Park',
        
        # Spring training venues
        'Tempe,US': 'Tempe Diablo Stadium',
        'Mesa,US': 'Sloan Park',
        'Scottsdale,US': 'Salt River Fields',
        'Peoria,US': 'Peoria Sports Complex',
        'Surprise,US': 'Surprise Stadium',
        'Goodyear,US': 'Goodyear Ballpark',
        'Fort Myers,US': 'Hammond Stadium',
        'Sarasota,US': 'Ed Smith Stadium',
        'Bradenton,US': 'LECOM Park',
        'Port Charlotte,US': 'Charlotte Sports Park',
        'Jupiter,US': 'Roger Dean Chevrolet Stadium',
        'West Palm Beach,US': 'The Ballpark of the Palm Beaches',
        'Clearwater,US': 'Spectrum Field',
        'Tampa,US': 'George M. Steinbrenner Field',
        'Dunedin,US': 'TD Ballpark'
    }
    
    return location_to_venue.get(location, 'Unknown Venue')

def get_venue_roof_info(venue_name):
    """
    Determine if venue has a roof and its type.
    Returns: {'has_roof': bool, 'type': 'fixed'|'retractable'|'open', 'should_alert': bool}
    """
    fixed_domes = {
        'Tropicana Field': {'has_roof': True, 'type': 'fixed', 'should_alert': False},
        'Rogers Centre': {'has_roof': True, 'type': 'fixed', 'should_alert': False}
    }
    
    retractable_roofs = {
        'Chase Field': {'has_roof': True, 'type': 'retractable'},
        'loanDepot park': {'has_roof': True, 'type': 'retractable'},
        'Globe Life Field': {'has_roof': True, 'type': 'retractable'},
        'Minute Maid Park': {'has_roof': True, 'type': 'retractable'},
        'T-Mobile Park': {'has_roof': True, 'type': 'retractable'},
        'American Family Field': {'has_roof': True, 'type': 'retractable'}
    }
    
    # Fixed dome - never alert
    if venue_name in fixed_domes:
        return fixed_domes[venue_name]
    
    # Retractable roof - need to check status
    if venue_name in retractable_roofs:
        return {**retractable_roofs[venue_name], 'should_alert': None}  # Will check API
    
    # Open-air stadium - always alert
    return {'has_roof': False, 'type': 'open', 'should_alert': True}

def get_roof_status_from_mlb(game_date, venue_name):
    """
    Check if retractable roof is open/closed for games today.
    Returns: True if should alert (roof open or unknown), False if roof closed
    """
    url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={game_date}&hydrate=venue"
    
    try:
        response = requests.get(url, timeout=5)
        data = response.json()
        
        if 'dates' in data and len(data['dates']) > 0:
            for date_info in data['dates']:
                for game in date_info.get('games', []):
                    game_venue = game['venue']['name']
                    
                    if game_venue == venue_name:
                        # Check if roof info exists in API response
                        venue_data = game.get('venue', {})
                        
                        # Some API responses include roof status
                        if 'roofType' in venue_data:
                            roof_type = venue_data.get('roofType', '').lower()
                            if roof_type == 'closed':
                                return False
                        
                        # If we can't determine roof status, alert to be safe
                        return True
        
        # Default to alerting if we can't find the game
        return True
        
    except Exception as e:
        print(f"   ⚠️  Error checking roof status for {venue_name}: {e}")
        # Default to alerting on error (safer for operations)
        return True

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
    pacific_tz = pytz.timezone('America/Los_Angeles')
    now = datetime.now(pacific_tz)
    
    if not high_risk_games:
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
                            "text": f"Checked at {now.strftime('%I:%M %p')} PT"
                        }
                    ]
                }
            ]
        }
    
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
                        "text": f"Updated: {now.strftime('%I:%M %p')} PT"
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
        
        game_block = {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*🔴 {game['opponent']}*\n{date_str} at {time_str}\n{weather_details}"
            }
        }
        
        message["blocks"].append(game_block)
        message["blocks"].append({"type": "divider"})
    
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
    try:
        games = load_games()
        
        # Check if any games exist at all
        if not games:
            print("ℹ️  No MLB games scheduled - skipping alert")
            log_workflow_run('skipped')
            return
        
        pacific_tz = pytz.timezone('America/Los_Angeles')
        now = datetime.now(pacific_tz)
        
        print(f"🏟️  Filtering games by roof status...")
        games_to_check = []
        
        for game in games:
            try:
                # Get venue information
                venue_name = get_venue_name_from_location(game['location'])
                roof_info = get_venue_roof_info(venue_name)
                
                # Fixed dome - skip weather check
                if roof_info['type'] == 'fixed':
                    print(f"   ⏭️  Skipping {game['opponent']} at {venue_name} (fixed dome)")
                    continue
                
                # Retractable roof - check if open/closed
                if roof_info['type'] == 'retractable':
                    should_alert = get_roof_status_from_mlb(game['date'], venue_name)
                    if should_alert:
                        print(f"   ✅ Including {game['opponent']} at {venue_name} (retractable roof open/unknown)")
                        games_to_check.append(game)
                    else:
                        print(f"   ⏭️  Skipping {game['opponent']} at {venue_name} (retractable roof closed)")
                    continue
                
                # Open-air stadium - always include
                print(f"   ✅ Including {game['opponent']} at {venue_name} (open-air)")
                games_to_check.append(game)
                
            except Exception as filter_error:
                print(f"   ⚠️  Error filtering {game.get('opponent', 'Unknown')}: {filter_error}")
                # Include game on error to be safe
                games_to_check.append(game)
                continue
        
        print(f"\n📊 Roof filtering: {len(games_to_check)} of {len(games)} games need weather monitoring\n")
        
        # If no games need monitoring after roof filtering, skip
        if not games_to_check:
            print("ℹ️  No games need weather monitoring (all in domed/closed-roof stadiums)")
            log_workflow_run('skipped')
            return
        
        high_risk_games = []
        
        print(f"🔍 Checking for high-risk weather games...")
        
        # Check if any games are in the next 48 hours
        upcoming_count = 0
        for game in games_to_check:
            game_datetime = datetime.strptime(f"{game['date']} {game['time']}", "%Y-%m-%d %H:%M")
            
            if now.replace(tzinfo=None) <= game_datetime <= now.replace(tzinfo=None) + timedelta(hours=48):
                upcoming_count += 1
                try:
                    weather = get_weather_forecast(game['location'], game_datetime)
                    
                    if is_high_risk(weather):
                        high_risk_games.append({
                            'game': game,
                            'weather': weather
                        })
                        print(f"  🔴 HIGH RISK: {game['opponent']} - {game['date']} {game['time']}")
                except Exception as weather_error:
                    print(f"  ⚠️  Error fetching weather for {game['opponent']}: {weather_error}")
                    continue
        
        # If no upcoming games at all, skip posting
        if upcoming_count == 0:
            print("ℹ️  No games in next 48 hours - skipping alert (off-day)")
            log_workflow_run('skipped')
            return
        
        print(f"\n📊 Found {len(high_risk_games)} high-risk game(s) out of {upcoming_count} total")
        
        # Post message (either high-risk alerts or all-clear)
        message = build_high_risk_message(high_risk_games)
        
        if post_to_slack(message):
            if high_risk_games:
                print(f"✅ High-risk alert posted for {len(high_risk_games)} game(s)")
                # ✅ LOG ANALYTICS - High-risk alert sent
                log_alert('high_risk')
            else:
                print("✅ All-clear message posted")
                # ✅ LOG ANALYTICS - All-clear message is also a high-risk check
                log_alert('high_risk')
            
            log_workflow_run('success')
        else:
            print("❌ Failed to post to Slack")
            log_workflow_run('failed')
            
    except Exception as e:
        print(f"❌ Fatal error in high-risk alert: {e}")
        log_workflow_run('failed')
        raise

if __name__ == "__main__":
    main()
