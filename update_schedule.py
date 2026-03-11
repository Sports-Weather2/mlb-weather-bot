import json
import requests
from datetime import datetime, timedelta
import pytz

def get_mlb_schedule(days_ahead=1):
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
                        game_datetime_utc = game['gameDate']
                        venue_name = game['venue']['name']
                        
                        venue_location = get_venue_location(venue_name)
                        venue_timezone = get_venue_timezone(venue_name)
                        
                        # Parse UTC time and convert to local venue time
                        game_dt_utc = datetime.strptime(game_datetime_utc, '%Y-%m-%dT%H:%M:%SZ')
                        game_dt_utc = pytz.utc.localize(game_dt_utc)
                        game_dt_local = game_dt_utc.astimezone(pytz.timezone(venue_timezone))
                        
                        games.append({
                            'date': game_dt_local.strftime('%Y-%m-%d'),
                            'time': game_dt_local.strftime('%H:%M'),
                            'opponent': f"{away_team} vs {home_team}",
                            'location': venue_location
                        })
        except Exception as e:
            print(f"Error fetching schedule for {date_str}: {e}")
            continue
    
    return games

def get_venue_timezone(venue_name):
    """Map venue to timezone"""
    arizona_venues = [
        'Tempe Diablo Stadium', 'Camelback Ranch', 'Sloan Park',
        'Salt River Fields', 'Peoria Sports Complex', 'Surprise Stadium',
        'Goodyear Ballpark', 'Hohokam Stadium', 'American Family Fields of Phoenix'
    ]
    
    florida_venues = [
        'JetBlue Park', 'Ed Smith Stadium', 'LECOM Park', 'Charlotte Sports Park',
        'Hammond Stadium', 'Roger Dean Chevrolet Stadium', 'Clover Park',
        'The Ballpark of the Palm Beaches', 'Spectrum Field',
        'George M. Steinbrenner Field', 'TD Ballpark'
    ]
    
    eastern_venues = [
        'Yankee Stadium', 'Citi Field', 'Citizens Bank Park', 'Nationals Park',
        'Fenway Park', 'Oriole Park at Camden Yards', 'Tropicana Field',
        'Truist Park', 'loanDepot park', 'PNC Park', 'Progressive Field',
        'Comerica Park', 'Great American Ball Park'
    ]
    
    central_venues = [
        'Wrigley Field', 'Guaranteed Rate Field', 'Busch Stadium',
        'American Family Field', 'Target Field', 'Kauffman Stadium',
        'Minute Maid Park', 'Globe Life Field'
    ]
    
    mountain_venues = ['Coors Field', 'Chase Field']
    
    pacific_venues = [
        'Angel Stadium', 'Dodger Stadium', 'Oracle Park', 'Petco Park', 'T-Mobile Park'
    ]
    
    if venue_name in arizona_venues:
        return 'America/Phoenix'
    elif venue_name in florida_venues:
        return 'America/New_York'
    elif venue_name in eastern_venues:
        return 'America/New_York'
    elif venue_name in central_venues:
        return 'America/Chicago'
    elif venue_name in mountain_venues:
        return 'America/Denver'
    elif venue_name in pacific_venues:
        return 'America/Los_Angeles'
    elif venue_name == 'Rogers Centre':
        return 'America/Toronto'
    else:
        return 'America/New_York'

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
        'LECOM Park': 'Bradenton,US',
        'Charlotte Sports Park': 'Port Charlotte,US',
        'Hammond Stadium': 'Fort Myers,US',
        'Roger Dean Chevrolet Stadium': 'Jupiter,US',
        'Clover Park': 'Port St Lucie,US',
        'The Ballpark of the Palm Beaches': 'West Palm Beach,US',
        'Spectrum Field': 'Clearwater,US',
        'George M. Steinbrenner Field': 'Tampa,US',
        'TD Ballpark': 'Dunedin,US',
    }
    
    regular_season_venues = {
        'Angel Stadium': 'Anaheim,US',
        'Dodger Stadium': 'Los Angeles,US',
        'Oracle Park': 'San Francisco,US',
        'Petco Park': 'San Diego,US',
        'Chase Field': 'Phoenix,US',
        'Coors Field': 'Denver,US',
        'T-Mobile Park': 'Seattle,US',
        'Globe Life Field': 'Arlington,US',
        'Minute Maid Park': 'Houston,US',
        'Kauffman Stadium': 'Kansas City,US',
        'Target Field': 'Minneapolis,US',
        'Guaranteed Rate Field': 'Chicago,US',
        'Progressive Field': 'Cleveland,US',
        'Comerica Park': 'Detroit,US',
        'Great American Ball Park': 'Cincinnati,US',
        'Busch Stadium': 'St Louis,US',
        'American Family Field': 'Milwaukee,US',
        'PNC Park': 'Pittsburgh,US',
        'Wrigley Field': 'Chicago,US',
        'Yankee Stadium': 'New York,US',
        'Citi Field': 'New York,US',
        'Citizens Bank Park': 'Philadelphia,US',
        'Nationals Park': 'Washington,US',
        'Fenway Park': 'Boston,US',
        'Oriole Park at Camden Yards': 'Baltimore,US',
        'Rogers Centre': 'Toronto,CA',
        'Tropicana Field': 'St Petersburg,US',
        'Truist Park': 'Atlanta,US',
        'loanDepot park': 'Miami,US',
    }
    
    if venue_name in spring_training_venues:
        return spring_training_venues[venue_name]
    elif venue_name in regular_season_venues:
        return regular_season_venues[venue_name]
    else:
        print(f"Warning: Unknown venue '{venue_name}', using default location")
        return "Phoenix,US"

def update_config_file(games):
    """Update config.json with fresh schedule"""
    config = {"games": games}
    
    with open('config.json', 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"✅ Updated config.json with {len(games)} games")

def main():
    print("🔄 Fetching MLB schedule...")
    games = get_mlb_schedule(days_ahead=1)
    
    if games:
        print(f"📅 Found {len(games)} games in next 24 hours")
        update_config_file(games)
    else:
        print("⚠️ No games found - keeping existing config.json")

if __name__ == "__main__":
    main()
