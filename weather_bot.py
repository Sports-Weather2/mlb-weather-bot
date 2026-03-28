import os
import json
import requests
import pytz
from datetime import datetime, timedelta
from analytics import log_alert, log_games_monitored, log_workflow_run

SLACK_WEBHOOK = os.environ.get('SLACK_WEBHOOK_URL')
WEATHER_API_KEY = os.environ.get('WEATHER_API_KEY')
WEATHER_BASE_URL = "https://api.openweathermap.org/data/2.5/forecast"

IMPACT_RULES = {
    'high_risk': {
        'rain_prob': 70,
        'wind_gust': 30,
        'lightning': True,
        'temp_extreme': [20, 100]
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
    
    if 'list' not in data:
        raise ValueError(f"No forecast data for {location}")
    
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
                "text": f"*⚾ {game['opponent']}*\n{date_str} at {time_str} PT"
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
    try:
        games = load_games()
        
        # Skip if no games scheduled at all (off-day)
        if not games:
            print("ℹ️  No MLB games scheduled - skipping report (off-day)")
            log_workflow_run('skipped')
            return
        
        pacific_tz = pytz.timezone('America/Los_Angeles')
        now = datetime.now(pacific_tz)
        today = now.strftime('%Y-%m-%d')
        
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
        
        upcoming_games = []
        
        print(f"🔍 Checking weather for {len(games_to_check)} games...")
        
        for game in games_to_check:
            try:
                game_datetime = datetime.strptime(
                    f"{game['date']} {game['time']}", 
                    "%Y-%m-%d %H:%M"
                )
                
                if now.replace(tzinfo=None) <= game_datetime <= now.replace(tzinfo=None) + timedelta(hours=48):
                    print(f"  📅 {game['opponent']} - {game['date']} {game['time']}")
                    
                    # Try to get weather with error handling
                    try:
                        weather = get_weather_forecast(game['location'], game_datetime)
                        impact = calculate_game_impact(weather)
                        
                        upcoming_games.append({
                            'game': game,
                            'weather': weather,
                            'impact': impact
                        })
                        
                        print(f"     {impact['emoji']} {impact['status']}")
                        
                    except Exception as weather_error:
                        print(f"     ❌ Error fetching weather for {game['location']}: {weather_error}")
                        print(f"     ⏭️  Skipping this game and continuing...")
                        continue
                        
            except Exception as game_error:
                print(f"  ❌ Error processing game {game.get('opponent', 'Unknown')}: {game_error}")
                continue
        
        # If no games in next 48 hours, skip (off-day)
        if not upcoming_games:
            print("ℹ️  No games in next 48 hours - skipping report (off-day)")
            log_workflow_run('skipped')
            return
        
        # Sort games by risk level: HIGH_RISK first, MONITOR second, CLEAR last
        risk_priority = {'HIGH_RISK': 0, 'MONITOR': 1, 'CLEAR': 2}
        upcoming_games.sort(key=lambda x: risk_priority[x['impact']['level']])
        
        print(f"\n📊 Games sorted by risk level (HIGH_RISK → MONITOR → CLEAR)")
        
        # Limit to 10 games to stay under Slack's 50-block limit
        if len(upcoming_games) > 10:
            print(f"⚠️ Limiting to top 10 games (total available: {len(upcoming_games)})")
            upcoming_games = upcoming_games[:10]
        
        # Only post if we have at least 1 game with successful weather data
        if upcoming_games:
            message = build_slack_message(upcoming_games)
            
            if post_to_slack(message):
                print(f"\n✅ Weather impact report posted for {len(upcoming_games)} game(s)")
                
                high_risk = sum(1 for g in upcoming_games if g['impact']['level'] == 'HIGH_RISK')
                monitor = sum(1 for g in upcoming_games if g['impact']['level'] == 'MONITOR')
                clear = sum(1 for g in upcoming_games if g['impact']['level'] == 'CLEAR')
                
                print(f"   🔴 High Risk: {high_risk}")
                print(f"   🟡 Monitor: {monitor}")
                print(f"   🟢 Clear: {clear}")
                
                # ✅ LOG ANALYTICS - Daily report sent
                log_alert('daily_report')
                log_games_monitored(len(upcoming_games))
                log_workflow_run('success')
            else:
                print("❌ Failed to post to Slack")
                log_workflow_run('failed')
        else:
            print("⚠️ No games with successful weather data - skipping report")
            log_workflow_run('skipped')
            
    except Exception as e:
        print(f"❌ Fatal error in weather bot: {e}")
        log_workflow_run('failed')
        raise

if __name__ == "__main__":
    main()
