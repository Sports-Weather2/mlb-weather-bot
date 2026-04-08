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
    Returns: True if should alert (roof confirmed open), False if roof closed or unknown
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
                            if roof_type == 'open':
                                print(f"   🔓 {venue_name} roof confirmed OPEN - including in alert")
                                return True
                            elif roof_type == 'closed':
                                print(f"   🔒 {venue_name} roof confirmed CLOSED - skipping alert")
                                return False
                        
                        # If we can't determine roof status, assume closed (reduce false positives)
                        print(f"   ❓ {venue_name} roof status unknown - assuming closed, skipping alert")
                        return False
        
        # Default to skipping if we can't find the game (reduce false positives)
        print(f"   ❓ {venue_name} game not found in API - assuming closed, skipping alert")
        return False
        
    except Exception as e:
        print(f"   ⚠️  Error checking roof status for {venue_name}: {e}")
        # Default to skipping on error (reduce false positives)
        print(f"   ❓ API error - assuming {venue_name} roof closed, skipping alert")
        return False

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
            "text": "✅
