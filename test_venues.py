import requests
import os

WEATHER_API_KEY = os.environ.get('WEATHER_API_KEY') or '1700eb25d6d9f0251666399e3c0dabd3'

def test_location(location_name, location_string):
    """Test if weather API can find this location"""
    url = f"https://api.openweathermap.org/data/2.5/forecast?q={location_string}&appid={WEATHER_API_KEY}&units=imperial"
    
    try:
        response = requests.get(url)
        data = response.json()
        
        if 'list' in data and len(data['list']) > 0:
            print(f"✅ {location_name:40} | {location_string:25} | WORKS")
            return True
        else:
            print(f"❌ {location_name:40} | {location_string:25} | FAILED: {data.get('message', 'Unknown error')}")
            return False
    except Exception as e:
        print(f"❌ {location_name:40} | {location_string:25} | ERROR: {e}")
        return False

def main():
    print("🔍 Testing All Venue Locations...\n")
    print(f"{'VENUE NAME':<40} | {'LOCATION STRING':<25} | STATUS")
    print("-" * 90)
    
    # Spring Training Venues
    print("\n🌵 SPRING TRAINING - ARIZONA (Cactus League):")
    spring_az = {
        'Tempe Diablo Stadium': 'Tempe,US',
        'Camelback Ranch': 'Phoenix,US',
        'Sloan Park': 'Mesa,US',
        'Salt River Fields': 'Scottsdale,US',
        'Peoria Sports Complex': 'Peoria,US',
        'Surprise Stadium': 'Surprise,US',
        'Goodyear Ballpark': 'Goodyear,US',
        'Hohokam Stadium': 'Mesa,US',
        'American Family Fields of Phoenix': 'Phoenix,US',
    }
    
    for venue, location in spring_az.items():
        test_location(venue, location)
    
    print("\n🌴 SPRING TRAINING - FLORIDA (Grapefruit League):")
    spring_fl = {
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
    
    for venue, location in spring_fl.items():
        test_location(venue, location)
    
    print("\n⚾ REGULAR SEASON STADIUMS:")
    regular = {
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
    
    for venue, location in regular.items():
        test_location(venue, location)
    
    print("\n" + "=" * 90)
    print("✅ Diagnostic complete!")

if __name__ == "__main__":
    main()
