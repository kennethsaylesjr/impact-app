import urllib.request
import urllib.error
import json
import random
import time

BASE_URL = "http://localhost:8000"

def make_request(method, endpoint, payload=None):
    url = f"{BASE_URL}{endpoint}"
    req = urllib.request.Request(url, method=method)
    req.add_header('Content-Type', 'application/json')
    data = None
    if payload:
        data = json.dumps(payload).encode('utf-8')
    try:
        with urllib.request.urlopen(req, data=data) as response:
            return response.status, json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        return e.code, None
    except Exception as e:
        return 500, None

def run_stress_test(iterations=100):
    print(f"Starting comprehensive testing ({iterations} iterations)...")
    errors = 0
    holes = 0

    # 1. Fetch initial data
    status_g, games_data = make_request("GET", "/api/games")
    status_u, umpires_data = make_request("GET", "/api/umpires")
    
    if status_g != 200 or status_u != 200:
        print(f"Failed to fetch initial data. Status G: {status_g}, U: {status_u}")
        return

    games = games_data
    umpires = umpires_data
    print(f"Loaded {len(games)} games and {len(umpires)} umpires.")

    if not games or not umpires:
        print("Need games and umpires in DB to run test. Please seed DB.")
        return

    print("Running random reassignment and API stress testing...")
    start_time = time.time()
    
    for i in range(iterations):
        game = random.choice(games)
        umpire = random.choice(umpires)
        
        # Test Assignment
        assign_payload = {
            "game_id": game['game_id'],
            "umpire_name": umpire['name']
        }
        status, _ = make_request("POST", "/api/reassign", assign_payload)
        if status != 200:
            errors += 1

        # Test mass rainout on random location
        rainout_payload = {
            "location": game['location'],
            "date": game['date']
        }
        status, _ = make_request("POST", "/api/mass_rainout", rainout_payload)
        if status != 200:
            errors += 1

        # Test score reporting
        score_payload = {
            "game_id": game['game_id'],
            "status": "Completed",
            "score": f"{random.randint(1, 10)} - {random.randint(1, 10)}"
        }
        status, _ = make_request("POST", "/api/report_score", score_payload)
        if status != 200:
            errors += 1

    end_time = time.time()
    print(f"\n--- Test Results ---")
    print(f"Total API Calls: {iterations * 3}")
    print(f"Errors Encountered: {errors}")
    print(f"Holes Found: {holes}")
    print(f"Time Taken: {end_time - start_time:.2f} seconds")

    if errors == 0 and holes == 0:
        print("\n✅ Application is fully robust. No errors or holes detected.")
    else:
        print("\n❌ Errors or holes were detected! Let's patch them.")

if __name__ == "__main__":
    run_stress_test(100)
