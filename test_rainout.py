import requests
import json

BASE_URL = "http://localhost:8000"

def test_mass_rainout():
    print("Testing Mass Rainout Feature...")
    
    # 1. Fetch current games
    res = requests.get(f"{BASE_URL}/api/data")
    data = res.json()
    games = data.get("games", [])
    
    if not games:
        print("No games to test. Please ensure DB has games.")
        return
        
    # Get a location from the games
    test_location = games[0]['location']
    test_date = games[0]['date']
    
    print(f"Targeting Location: {test_location} on {test_date}")
    
    # 2. Trigger Mass Rainout
    payload = {
        "location": test_location,
        "date": test_date
    }
    
    res = requests.post(f"{BASE_URL}/api/mass_rainout", json=payload)
    if res.status_code == 200:
        result = res.json()
        print(f"Success! Rained out {result['updated']} games.")
    else:
        print(f"Failed! Status code: {res.status_code}")
        print(res.text)

if __name__ == "__main__":
    test_mass_rainout()
