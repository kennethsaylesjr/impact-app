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
    unique_ump_a = f"Tester {iteration}-A"
    unique_ump_b = f"Tester {iteration}-B"
    
    # 1. Test Game Importer
    game_payload = {
        "games": [
            {"date": f"2030-01-{iteration:02d}", "time": "10:00", "location": f"Field A{iteration}"},
            {"date": f"2030-01-{iteration:02d}", "time": "12:00", "location": f"Field B{iteration}"},
            {"date": f"2030-01-{iteration:02d}", "time": "14:00", "location": f"Field C{iteration}"}
        ]
    }
    game_res = post("/api/import_games", game_payload)
    if not game_res.get('success') or game_res.get('inserted') != 3:
        print(f"[Iter {iteration}] Game Import failed: {game_res}")
        errors += 1

    # 2. Test Roster Importer (Include one EXPIRED and one VALID)
    ump_payload = {
        "umpires": [
            {"name": unique_ump_a, "phone_number": "111", "level": "Junior", "pay_rate": 40.0, "registration_expiry": "2030-01-01", "background_check_expiry": "2030-01-01"},
            {"name": unique_ump_b, "phone_number": "222", "level": "Senior", "pay_rate": 70.0, "registration_expiry": "2020-01-01", "background_check_expiry": "2020-01-01"}
        ]
    }
    ump_res = post("/api/import_roster", ump_payload)
    if not ump_res.get('success') or ump_res.get('inserted') != 2:
        print(f"[Iter {iteration}] Umpire Import failed: {ump_res}")
        errors += 1
        
    games = get("/api/games")
    # Find the 3 games we just inserted
    my_games = [g for g in games if g['date'] == f"2030-01-{iteration:02d}"]
    if len(my_games) < 3:
        print(f"[Iter {iteration}] Missing imported games")
        return errors + 1
        
    g1, g2, g3 = my_games[0]['game_id'], my_games[1]['game_id'], my_games[2]['game_id']
    
    # 3. Test Assignment
    r1 = post("/api/reassign", {"game_id": g1, "umpire_name": unique_ump_a})
    r2 = post("/api/reassign", {"game_id": g2, "umpire_name": unique_ump_b})
    r3 = post("/api/reassign", {"game_id": g3, "umpire_name": unique_ump_a})
    
    # Conflict Resolution Override: B steals g3 from A
    r4 = post("/api/reassign", {"game_id": g3, "umpire_name": unique_ump_b})
    
    # 4. Test Score / Status Reporting
    s1 = post("/api/report_score", {"game_id": g1, "status": "Completed", "score": "5-2"})
    s2 = post("/api/report_score", {"game_id": g2, "status": "Rained Out", "score": ""})
    
    if not s1.get('success') or not s2.get('success'):
        print(f"[Iter {iteration}] Score report failed")
        errors += 1
    
    # 5. Verify Data State
    final_games = get("/api/games")
    final_umpires = get("/api/umpires")
    
    fg1 = next((g for g in final_games if g['game_id'] == g1), None)
    if fg1['status'] != 'Completed' or fg1['score'] != '5-2':
        print(f"[Iter {iteration}] Game 1 state incorrect")
        errors += 1
        
    found_a_payroll = 0
    found_b_payroll = 0
    
    for u in final_umpires:
        assigned = [g for g in final_games if g['umpire_id'] == u['id']]
        payout = len(assigned) * u['pay_rate']
        if u['name'] == unique_ump_a:
            found_a_payroll = payout
        if u['name'] == unique_ump_b:
            found_b_payroll = payout
            
    # Umpire A only has g1 = 1 game * $40
    if found_a_payroll != 40.0:
        print(f"[Iter {iteration}] Error: Umpire A payroll {found_a_payroll} != 40")
        errors += 1
        
    # Umpire B has g2, g3 = 2 games * $70
    if found_b_payroll != 140.0:
        print(f"[Iter {iteration}] Error: Umpire B payroll {found_b_payroll} != 140")
        errors += 1
        
    return errors

total_errors = 0
print(f"Running 100 iteration FULL stress test...")
for i in range(1, 101):
    err = run_suite(i)
    total_errors += err
    if i % 10 == 0:
        print(f"Completed {i}/100 iterations... Current Errors: {total_errors}")

print(f"\n100-Iteration Extreme Stress Test complete. Total Errors: {total_errors}")
