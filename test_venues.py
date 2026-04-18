# test_venues.py
# Updated: April 2026
# Tests NWS API connectivity for all MLB stadium coordinates
# No API key required — NWS is free and open
# Run manually via test-venues.yml workflow

import requests

NWS_USER_AGENT = "MLBWeatherBot/2.0 (github.com/Sports-Weather2/mlb-weather-bot)"

# All stadium coordinates — matches STADIUM_COORDINATES in weather_bot.py
VENUES = {
    # ── Fixed Dome — excluded from weather alerts ──────────────
    'Tropicana Field (Fixed Dome)':         {'lat': 27.7683, 'lon': -82.6534},
    'Rogers Centre (Fixed Dome)':           {'lat': 43.6414, 'lon': -79.3894},

    # ── Retractable Roof ───────────────────────────────────────
    'Chase Field':                          {'lat': 33.4453, 'lon': -112.0667},
    'loanDepot park':                       {'lat': 25.7781, 'lon': -80.2197},
    'Globe Life Field':                     {'lat': 32.7512, 'lon': -97.0832},
    'Minute Maid Park':                     {'lat': 29.7573, 'lon': -95.3555},
    'T-Mobile Park':                        {'lat': 47.5914, 'lon': -122.3325},
    'American Family Field':                {'lat': 43.0280, 'lon': -87.9712},

    # ── Open Air — Regular Season ──────────────────────────────
    'Angel Stadium':                        {'lat': 33.8003, 'lon': -117.8827},
    'Dodger Stadium':                       {'lat': 34.0739, 'lon': -118.2400},
    'Oracle Park':                          {'lat': 37.7786, 'lon': -122.3893},
    'Petco Park':                           {'lat': 32.7076, 'lon': -117.1570},
    'Coors Field':                          {'lat': 39.7559, 'lon': -104.9942},
    'Kauffman Stadium':                     {'lat': 39.0517, 'lon': -94.4803},
    'Target Field':                         {'lat': 44.9817, 'lon': -93.2776},
    'Guaranteed Rate Field':                {'lat': 41.8299, 'lon': -87.6338},
    'Progressive Field':                    {'lat': 41.4962, 'lon': -81.6852},
    'Comerica Park':                        {'lat': 42.3390, 'lon': -83.0485},
    'Great American Ball Park':             {'lat': 39.0979, 'lon': -84.5082},
    'Busch Stadium':                        {'lat': 38.6226, 'lon': -90.1928},
    'PNC Park':                             {'lat': 40.4469, 'lon': -80.0057},
    'Wrigley Field':                        {'lat': 41.9484, 'lon': -87.6553},
    'Yankee Stadium':                       {'lat': 40.8296, 'lon': -73.9262},
    'Citi Field':                           {'lat': 40.7571, 'lon': -73.8458},
    'Citizens Bank Park':                   {'lat': 39.9061, 'lon': -75.1665},
    'Nationals Park':                       {'lat': 38.8730, 'lon': -77.0074},
    'Fenway Park':                          {'lat': 42.3467, 'lon': -71.0972},
    'Oriole Park at Camden Yards':          {'lat': 39.2838, 'lon': -76.6216},
    'Truist Park':                          {'lat': 33.8907, 'lon': -84.4677},
    'Sutter Health Park (Athletics)':       {'lat': 37.7516, 'lon': -122.2005},

    # ── Spring Training — Cactus League (AZ) ──────────────────
    'Tempe Diablo Stadium':                 {'lat': 33.4255, 'lon': -111.9400},
    'Camelback Ranch':                      {'lat': 33.5053, 'lon': -112.1911},
    'Sloan Park':                           {'lat': 33.3978, 'lon': -111.8336},
    'Salt River Fields':                    {'lat': 33.4569, 'lon': -111.9456},
    'Peoria Sports Complex':                {'lat': 33.5806, 'lon': -112.2374},
    'Surprise Stadium':                     {'lat': 33.6284, 'lon': -112.3681},
    'Goodyear Ballpark':                    {'lat': 33.4350, 'lon': -112.3750},
    'American Family Fields of Phoenix':    {'lat': 33.4797, 'lon': -112.1347},

    # ── Spring Training — Grapefruit League (FL) ──────────────
    'JetBlue Park':                         {'lat': 26.6417, 'lon': -81.8557},
    'Ed Smith Stadium':                     {'lat': 27.3364, 'lon': -82.4625},
    'LECOM Park':                           {'lat': 27.5001, 'lon': -82.5748},
    'Charlotte Sports Park':                {'lat': 26.9787, 'lon': -82.1087},
    'Hammond Stadium':                      {'lat': 26.6417, 'lon': -81.8557},
    'Roger Dean Chevrolet Stadium':         {'lat': 26.9134, 'lon': -80.1165},
    'Clover Park':                          {'lat': 27.2719, 'lon': -80.3865},
    'The Ballpark of the Palm Beaches':     {'lat': 26.7153, 'lon': -80.0534},
    'Spectrum Field':                       {'lat': 27.9659, 'lon': -82.7291},
    'George M. Steinbrenner Field':         {'lat': 27.9711, 'lon': -82.5038},
    'TD Ballpark':                          {'lat': 28.0194, 'lon': -82.7693},
}


def test_nws_venue(venue_name, lat, lon):
    """
    Test NWS API connectivity for a stadium lat/lon.
    Step 1: Get gridpoint URL
    Step 2: Fetch hourly forecast
    Returns True if both steps succeed.
    """
    headers = {
        'User-Agent': NWS_USER_AGENT,
        'Accept': 'application/geo+json'
    }

    # ── Step 1: Points lookup ──────────────────────────────────
    points_url = f"https://api.weather.gov/points/{lat},{lon}"
    try:
        resp = requests.get(points_url, headers=headers, timeout=10)

        if resp.status_code != 200:
            print(f"❌ {venue_name:<45} | FAILED points lookup: HTTP {resp.status_code}")
            return False

        props        = resp.json().get('properties', {})
        hourly_url   = props.get('forecastHourly')
        grid_id      = props.get('gridId', '?')
        grid_x       = props.get('gridX', '?')
        grid_y       = props.get('gridY', '?')
        tz           = props.get('timeZone', '?')

        if not hourly_url:
            print(f"❌ {venue_name:<45} | FAILED: No hourly URL in response")
            return False

    except requests.exceptions.Timeout:
        print(f"❌ {venue_name:<45} | ERROR: Points request timed out")
        return False
    except Exception as e:
        print(f"❌ {venue_name:<45} | ERROR: {e}")
        return False

    # ── Step 2: Hourly forecast fetch ─────────────────────────
    try:
        resp2 = requests.get(hourly_url, headers=headers, timeout=10)

        if resp2.status_code != 200:
            print(f"❌ {venue_name:<45} | FAILED hourly fetch: HTTP {resp2.status_code}")
            return False

        periods = resp2.json().get('properties', {}).get('periods', [])

        if not periods:
            print(f"❌ {venue_name:<45} | FAILED: No forecast periods returned")
            return False

        # Show first period as sample
        first         = periods[0]
        temp          = first.get('temperature', '?')
        unit          = first.get('temperatureUnit', 'F')
        forecast      = first.get('shortForecast', '?')
        pop           = first.get('probabilityOfPrecipitation', {})
        rain_pct      = pop.get('value', 0) if isinstance(pop, dict) else 0

        print(f"✅ {venue_name:<45} | {grid_id}/{grid_x},{grid_y} | "
              f"{tz:<30} | {temp}°{unit} | {rain_pct}% rain | {forecast}")
        return True

    except requests.exceptions.Timeout:
        print(f"❌ {venue_name:<45} | ERROR: Hourly forecast request timed out")
        return False
    except Exception as e:
        print(f"❌ {venue_name:<45} | ERROR: {e}")
        return False


def main():
    print("🔍 Testing NWS API for All MLB Venue Coordinates...\n")
    print(f"{'VENUE NAME':<45} | {'NWS GRID':<20} | {'TIMEZONE':<30} | FORECAST SAMPLE")
    print("-" * 130)

    sections = {
        "🏟️  FIXED DOME STADIUMS (excluded from alerts)": [
            'Tropicana Field (Fixed Dome)',
            'Rogers Centre (Fixed Dome)'
        ],
        "🔄 RETRACTABLE ROOF STADIUMS": [
            'Chase Field', 'loanDepot park', 'Globe Life Field',
            'Minute Maid Park', 'T-Mobile Park', 'American Family Field'
        ],
        "☀️  OPEN AIR — REGULAR SEASON": [
            'Angel Stadium', 'Dodger Stadium', 'Oracle Park', 'Petco Park',
            'Coors Field', 'Kauffman Stadium', 'Target Field',
            'Guaranteed Rate Field', 'Progressive Field', 'Comerica Park',
            'Great American Ball Park', 'Busch Stadium', 'PNC Park',
            'Wrigley Field', 'Yankee Stadium', 'Citi Field',
            'Citizens Bank Park', 'Nationals Park', 'Fenway Park',
            'Oriole Park at Camden Yards', 'Truist Park',
            'Sutter Health Park (Athletics)'
        ],
        "🌵 SPRING TRAINING — CACTUS LEAGUE (AZ)": [
            'Tempe Diablo Stadium', 'Camelback Ranch', 'Sloan Park',
            'Salt River Fields', 'Peoria Sports Complex', 'Surprise Stadium',
            'Goodyear Ballpark', 'American Family Fields of Phoenix'
        ],
        "🌴 SPRING TRAINING — GRAPEFRUIT LEAGUE (FL)": [
            'JetBlue Park', 'Ed Smith Stadium', 'LECOM Park',
            'Charlotte Sports Park', 'Hammond Stadium',
            'Roger Dean Chevrolet Stadium', 'Clover Park',
            'The Ballpark of the Palm Beaches', 'Spectrum Field',
            'George M. Steinbrenner Field', 'TD Ballpark'
        ]
    }

    total   = 0
    passed  = 0
    failed  = 0

    for section_name, venue_list in sections.items():
        print(f"\n{section_name}:")
        for venue in venue_list:
            if venue in VENUES:
                coords  = VENUES[venue]
                result  = test_nws_venue(venue, coords['lat'], coords['lon'])
                total  += 1
                if result:
                    passed += 1
                else:
                    failed += 1

    print("\n" + "=" * 130)
    print(f"📊 Results: {passed}/{total} venues passed  |  "
          f"{'✅ All good!' if failed == 0 else f'❌ {failed} venue(s) need attention'}")
    print("🌐 Source: National Weather Service (NWS) API — no API key required")
    print("=" * 130)


if __name__ == "__main__":
    main()
