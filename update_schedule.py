import json
import requests
from datetime import datetime, timedelta

def get_mlb_schedule(days_ahead=2):
    """Fetch MLB schedule for next X days using MLB Stats API"""
    games = []
    
    for day_offset in range(days_ahead):
        date = datetime.now() + timedelta(days=day_offset)
        date_str = date.strftime('%Y-%m-%d')
        
        url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={date_str}"
        
        try:
            response = requests.get(url)
            data = response.json()
            
            if 'dates' in data and len(data['dates']) > 0:
                for date_info in data['dates']:
                    for game in date_info.get('games', []):
                        away_team = game['teams']['away']['team']['name']
                        home_team = game['teams']['home']['team']['name']
                        game_datetime = game['gameDate']
                        venue_name = game['venue']['name']
                        
                        venue_location = get_venue_location(venue_name)
                        
                        game_dt = datetime.strptime(game_datetime, '%Y-%m-%dT%H:%M:%SZ')
                        
                        games.append({
                            'date': game_dt.strftime('%Y-%m-%d'),
                            'time': game_dt.strftime('%H:%M'),
                            'opponent': f"{away_team} vs {home_team}",
                            'location': venue_location
                        })
        except Exception as e:
            print(f"Error fetching schedule for {date_str}: {e}")
            continue
    
    return games

def get_venue_location(venue_name):
    """Map venue names to locations for weather API"""
    spring_training_venues = {
        'Tempe Diablo Stadium': 'Tempe,US',
        'Camelback Ranch': 'Phoenix,US',
        'Sloan Park': 'Mesa,US',
        'Salt River Fields': 'Scottsdale,US',
        'Peoria Sports Complex': 'Peoria,US',
        'Surprise Stadium': 'Surprise,US',
        'Goodyear Ballpark': 'Goodyear,US',
        'Hohokam Stadium': 'Mesa,US',
        'American Family Fields of Phoenix': 'Phoenix,US',
        'JetBlue Park': 'Fort Myers,US',
        'Ed Smith Stadium': 'Sarasota,US',
        'LE
