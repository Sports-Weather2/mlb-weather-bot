import requests
import os

WEATHER_API_KEY = os.environ.get('WEATHER_API_KEY')

if not WEATHER_API_KEY:
    raise ValueError("❌ WEATHER_API_KEY environment variable not set")

def test_location(location_name, location_string):
    """Test if weather API can find this location"""
    
    url = "https://api.openweathermap.org/data/2.5/forecast"
    params = {
        "q": location_string,
        "appid": WEATHER_API_KEY,
        "units": "imperial"
    }

    try:
        response = requests.get(url, params=params, timeout=10)

        if response.status_code != 200:
            print(f"❌ {location_name:40} | {location_string:25} | FAILED: HTTP {response.status_code}")
            return False

        data = response.json()

        if 'list' in data and len(data['list']) > 0:
            print(f"✅ {location_name:40} | {location_string:25} | WORKS")
            return True
        else:
            print(f"❌ {location_name:40} | {location_string:25} | FAILED: {data.get('message', 'Unknown error')}")
            return False

    except requests.exceptions.Timeout:
        print(f"❌ {location_name:40} | {location_string:25} | ERROR: Request timed out")
        return False
    except Exception as e:
        print(f"❌ {location_name:40} | {location_string:25} | ERROR: {e}")
        return False


def main():
    print("🔍 Testing All Venue Locations...\n")
    print(f"{'VENUE NAME':<40} | {'LOCATION STRING':<25} | STATUS")
    print("-" * 90)

    # 🌵 SPRING TRAINING - ARIZONA (Cactus League)
    print("\n🌵 SPRING TRAINING - ARIZONA (Cactus League):")
    spring_az = {
        'Tempe Diablo Stadium': '85281,US',
        'Camelback Ranch': '85037,US',
        'Sloan Park': '85201,US',
        'Salt River Fields': '85256,US',
        'Peoria Sports Complex': '85345,US',
        'Surprise Stadium': '85374,US',
        'Goodyear Ballpark': '85338,US',
        'Hohokam Stadium': '85204,US',
        'American Family Fields of Phoenix': '85009,US',
    }

    for venue, location in spring_az.items():
        test_location(venue, location)

    # 🌴 SPRING TRAINING - FLORIDA (Grapefruit League)
    print("\n🌴 SPRING TRAINING - FLORIDA (Grapefruit League):")
    spring_fl = {
        'JetBlue Park': '33913,US',
        'Ed Smith Stadium': '34237,US',
        'LECOM Park': '34205,US',
        'Charlotte Sports Park': '33954,US',
        'Hammond Stadium': '33905,US',
        'Roger Dean Chevrolet Stadium': '33458,US',
        'Clover Park': '34986,US',  # FIXED (was Port St Lucie)
        'The Ballpark of the Palm Beaches': '33407,US',
        'Spectrum Field': '33765,US',
        'George M. Steinbrenner Field': '33607,US',
        'TD Ballpark': '34698,US',
    }

    for venue, location in spring_fl.items():
        test_location(venue, location)

    # ⚾ REGULAR SEASON STADIUMS
    print("\n⚾ REGULAR SEASON STADIUMS:")
    regular = {
        'Angel Stadium': '92806,US',
        'Dodger Stadium': '90012,US',
        'Oracle Park': '94107,US',
        'Petco Park': '92101,US',
        'Chase Field': '85004,US',
        'Coors Field': '80205,US',
        'T-Mobile Park': '98134,US',
        'Globe Life Field': '76011,US',
        'Minute Maid Park': '77002,US',
        'Kauffman Stadium': '64129,US',
        'Target Field': '55403,US',
        'Guaranteed Rate Field': '60616,US',
        'Progressive Field': '44115,US',
        'Comerica Park': '48201,US',
        'Great American Ball Park': '45202,US',
        'Busch Stadium': '63102,US',
        'American Family Field': '53214,US',
        'PNC Park': '15212,US',
        'Wrigley Field': '60613,US',
        'Yankee Stadium': '10451,US',
        'Citi Field': '11368,US',
        'Citizens Bank Park': '19148,US',
        'Nationals Park': '20003,US',
        'Fenway Park': '02215,US',
        'Oriole Park at Camden Yards': '21201,US',
        'Rogers Centre': 'M5V1J1,CA',
        'Tropicana Field': '33705,US',
        'Truist Park': '30339,US',
        'loanDepot park': '33125,US',
    }

    for venue, location in regular.items():
        test_location(venue, location)

    print("\n" + "=" * 90)
    print("✅ Diagnostic complete!")


if __name__ == "__main__":
    main()
