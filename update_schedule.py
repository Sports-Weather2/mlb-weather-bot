# update_schedule.py
# Updated: April 2026
# Changes:
#   - Added game_pk to each game entry (required for prediction accuracy tracking)
#   - Added missing/updated Regular Season venues (Athletics → Sacramento, etc.)
#   - Added Sutter Health Park (Athletics)
#   - Removed stale Oakland Coliseum entry
#   - Added timeout to requests call
#   - Added unknown venue warning with full list for easier debugging

import json
import requests
from datetime import datetime, timedelta
import pytz

def get_mlb_schedule(days_ahead=1):
    """Fetch MLB schedule for next X days using MLB Stats API"""
    games = []
    pacific_tz = pytz.timezone('America/Los_Angeles')

    for day_offset in range(days_ahead):
        date = datetime.now() + timedelta(days=day_offset)
        date_str = date.strftime('%Y-%m-%d')

        url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={date_str}"

        try:
            response = requests.get(url, timeout=10)
            data = response.json()

            if 'dates' in data and len(data['dates']) > 0:
                for date_info in data['dates']:
                    for game in date_info.get('games', []):
                        away_team      = game['teams']['away']['team']['name']
                        home_team      = game['teams']['home']['team']['name']
                        game_datetime_utc = game['gameDate']
                        venue_name     = game['venue']['name']
                        game_pk        = game.get('gamePk', '')  # ✅ Added for accuracy tracking

                        venue_location = get_venue_location(venue_name)

                        # Parse UTC time and convert to Pacific
                        game_dt_utc     = datetime.strptime(game_datetime_utc, '%Y-%m-%dT%H:%M:%SZ')
                        game_dt_utc     = pytz.utc.localize(game_dt_utc)
                        game_dt_pacific = game_dt_utc.astimezone(pacific_tz)

                        games.append({
                            'date':     game_dt_pacific.strftime('%Y-%m-%d'),
                            'time':     game_dt_pacific.strftime('%H:%M'),
                            'opponent': f"{away_team} vs {home_team}",
                            'location': venue_location,
                            'venue':    venue_name,            # ✅ Added for debugging
                            'game_pk':  game_pk                # ✅ Added for accuracy tracking
                        })

        except Exception as e:
            print(f"Error fetching schedule for {date_str}: {e}")
            continue

    return games


def get_venue_location(venue_name):
    """
    Map MLB venue names to location strings.
    Location strings must exactly match keys in STADIUM_COORDINATES
    in weather_bot.py and high_risk_alert.py.
    """

    # ── Spring Training — Cactus League (AZ) ──────────────────
    spring_training_venues = {
        'Tempe Diablo Stadium':              'Tempe,US',
        'Camelback Ranch':                   'Phoenix,US',
        'Sloan Park':                        'Mesa,US',
        'Salt River Fields':                 'Scottsdale,US',
        'Salt River Fields at Talking Stick':'Scottsdale,US',  # ✅ alternate MLB API name
        'Peoria Sports Complex':             'Peoria,US',
        'Surprise Stadium':                  'Surprise,US',
        'Goodyear Ballpark':                 'Goodyear,US',
        'Hohokam Stadium':                   'Mesa,US',
        'American Family Fields of Phoenix': 'Phoenix,US',
        'JetBlue Park':                      'Fort Myers,US',
        'JetBlue Park at Fenway South':      'Fort Myers,US',  # ✅ alternate MLB API name
        'Ed Smith Stadium':                  'Sarasota,US',
        'LECOM Park':                        'Bradenton,US',
        'Charlotte Sports Park':             'Port Charlotte,US',
        'Hammond Stadium':                   'Fort Myers,US',
        'Roger Dean Chevrolet Stadium':      'Jupiter,US',
        'Clover Park':                       'West Palm Beach,US',
        'The Ballpark of the Palm Beaches':  'West Palm Beach,US',
        'Spectrum Field':                    'Clearwater,US',
        'George M. Steinbrenner Field':      'Tampa,US',
        'TD Ballpark':                       'Dunedin,US',
    }

    # ── Regular Season ─────────────────────────────────────────
    regular_season_venues = {
        # AL West
        'Angel Stadium':                 'Anaheim,US',
        'Dodger Stadium':                'Los Angeles,US',
        'T-Mobile Park':                 'Seattle,US',
        'Globe Life Field':              'Arlington,US',
        'Minute Maid Park':              'Houston,US',
        'Sutter Health Park':            'Oakland,US',    # ✅ Athletics (Sacramento)

        # AL Central
        'Kauffman Stadium':              'Kansas City,US',
        'Target Field':                  'Minneapolis,US',
        'Guaranteed Rate Field':         'Chicago,US',
        'Progressive Field':             'Cleveland,US',
        'Comerica Park':                 'Detroit,US',

        # AL East
        'Yankee Stadium':                'New York,US',
        'Fenway Park':                   'Boston,US',
        'Oriole Park at Camden Yards':   'Baltimore,US',
        'Rogers Centre':                 'Toronto,CA',    # Excluded — roof always closed
        'Tropicana Field':               'St Petersburg,US',

        # NL West
        'Oracle Park':                   'San Francisco,US',
        'Petco Park':                    'San Diego,US',
        'Chase Field':                   'Phoenix,US',
        'Coors Field':                   'Denver,US',

        # NL Central
        'Great American Ball Park':      'Cincinnati,US',
        'Busch Stadium':                 'St Louis,US',
        'American Family Field':         'Milwaukee,US',
        'PNC Park':                      'Pittsburgh,US',
        'Wrigley Field':                 'Chicago,US',

        # NL East
        'Citi Field':                    'New York,US',
        'Citizens Bank Park':            'Philadelphia,US',
        'Nationals Park':                'Washington,US',
        'Truist Park':                   'Atlanta,US',
        'loanDepot park':                'Miami,US',
    }

    if venue_name in spring_training_venues:
        return spring_training_venues[venue_name]
    elif venue_name in regular_season_venues:
        return regular_season_venues[venue_name]
    else:
        # ✅ Improved warning — shows exact venue name for easy debugging
        print(f"⚠️  WARNING: Unknown venue '{venue_name}' — defaulting to Phoenix,US")
        print(f"   👉 Add '{venue_name}' to get_venue_location() in update_schedule.py")
        return 'Phoenix,US'


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

        # Print venue summary for easy verification
        print(f"\n📍 Venues in today's schedule:")
        seen_venues = set()
        for game in games:
            venue = game.get('venue', 'Unknown')
            if venue not in seen_venues:
                print(f"   • {venue} → {game['location']}")
                seen_venues.add(venue)

        update_config_file(games)
    else:
        print("⚠️  No games found - keeping existing config.json")


if __name__ == "__main__":
    main()
