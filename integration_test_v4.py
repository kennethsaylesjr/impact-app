import urllib.request
import urllib.error
import json
import random

BASE_URL = "http://localhost:8000"

def post(endpoint, payload):
    req = urllib.request.Request(
        f"{BASE_URL}{endpoint}",
        data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode())
    except urllib.error.HTTPError as e:
        return {"error": e.code, "message": e.read().decode()}

def get(endpoint):
    try:
        with urllib.request.urlopen(f"{BASE_URL}{endpoint}") as response:
            return json.loads(response.read().decode())
    except urllib.error.HTTPError as e:
        return {"error": e.code, "message": e.read().decode()}

def run_suite(iteration):
    errors = 0
    unique_name_a = f"Umpire Alpha {iteration}"
    unique_name_b = f"Umpire Beta {iteration}"
    
    initial_umpires = get("/api/umpires")
    if 'error' in initial_umpires:
        print(f"API Error on init: {initial_umpires}")
        return 1

    import_payload = {
        "umpires": [
            {"name": unique_name_a, "phone_number": "111", "level": "Junior", "pay_rate": 40.0, "registration_expiry": "2030-01-01", "background_check_expiry": "2030-01-01"},
            {"name": unique_name_b, "phone_number": "222", "level": "Senior", "pay_rate": 70.0, "registration_expiry": "2030-01-01", "background_check_expiry": "2030-01-01"}
        ]
    }
    
    res = post("/api/import_roster", import_payload)
    if not res.get("success") or res.get("inserted") != 2:
        print(f"[Iter {iteration}] Import failed: {res}")
        errors += 1
        
    games = get("/api/games")
    if len(games) < 3:
        print(f"[Iter {iteration}] Not enough games")
        return errors
        
    g1, g2, g3 = random.sample(games, 3)
    g1_id, g2_id, g3_id = g1['game_id'], g2['game_id'], g3['game_id']
    
    r1 = post("/api/reassign", {"game_id": g1_id, "umpire_name": unique_name_a})
    r2 = post("/api/reassign", {"game_id": g2_id, "umpire_name": unique_name_a})
    r3 = post("/api/reassign", {"game_id": g3_id, "umpire_name": unique_name_b})
    r4 = post("/api/reassign", {"game_id": g1_id, "umpire_name": unique_name_b})
    
    if not r1.get('success') or not r2.get('success') or not r3.get('success') or not r4.get('success'):
        print(f"[Iter {iteration}] Reassign failed. r1: {r1}, r2: {r2}, r3: {r3}, r4: {r4}")
        errors += 1
    
    final_games = get("/api/games")
    final_umpires = get("/api/umpires")
    
    found_a_payroll = 0
    found_b_payroll = 0
    
    for u in final_umpires:
        assigned = [g for g in final_games if g['umpire_id'] == u['id']]
        payout = len(assigned) * u['pay_rate']
        if u['name'] == unique_name_a:
            found_a_payroll = payout
        if u['name'] == unique_name_b:
            found_b_payroll = payout
            
    if found_a_payroll != 40.0:
        print(f"[Iter {iteration}] Error: Umpire A payroll incorrect. Expected 40, got {found_a_payroll}")
        errors += 1
        
    if found_b_payroll != 140.0:
        print(f"[Iter {iteration}] Error: Umpire B payroll incorrect. Expected 140, got {found_b_payroll}")
        errors += 1
        
    return errors

total_errors = 0
print(f"Running 50 iteration extreme stress test...")
for i in range(1, 51):
    total_errors += run_suite(i)

print(f"\nTotal Errors: {total_errors}")
