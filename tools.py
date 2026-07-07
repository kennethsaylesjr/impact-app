from typing import List, Dict
import database
from datetime import datetime

def get_unassigned_games() -> List[Dict]:
    """Returns a list of upcoming games that have no umpire assigned."""
    return database.execute_query("SELECT * FROM games WHERE umpire_id IS NULL")

def get_available_umpires() -> List[Dict]:
    """Returns a list of umpires who are currently available, including their details."""
    return database.execute_query("SELECT * FROM umpires WHERE available = 1")

def check_credentials(umpire_name: str) -> str:
    """Checks the credential expiration dates for a specific umpire."""
    umpires = database.execute_query("SELECT * FROM umpires WHERE name = ?", (umpire_name,))
    if not umpires:
        return f"Error: Umpire '{umpire_name}' not found."
    
    u = umpires[0]
    return f"Credentials for {u['name']}:\n- Registration expires: {u['registration_expiry']}\n- Background Check expires: {u['background_check_expiry']}"

def assign_umpire_to_game(game_id: int, umpire_name: str) -> str:
    """Assigns an umpire to a game. Protects against expired credentials, unavailability, overwriting, and double-booking."""
    
    # 1. Look up the umpire ID and credentials
    umpires = database.execute_query("SELECT * FROM umpires WHERE name = ?", (umpire_name,))
    if not umpires:
        return f"Error: Umpire '{umpire_name}' not found."
    umpire = umpires[0]
    
    # 2. Check if umpire is marked available (Admin Override: Allow but warn)
    warning_msg = ""
    if not umpire['available']:
        warning_msg = f" (Warning: Forced assignment - {umpire['name']} was marked as unavailable)"

    # 3. Validate Credentials
    current_date = datetime.now().strftime("%Y-%m-%d")
    if umpire['registration_expiry'] < current_date:
        return f"Assignment Blocked: {umpire['name']}'s registration expired on {umpire['registration_expiry']}."
    if umpire['background_check_expiry'] < current_date:
        return f"Assignment Blocked: {umpire['name']}'s background check expired on {umpire['background_check_expiry']}."
    
    # 4. Check if the game exists and is not already assigned
    games = database.execute_query("SELECT * FROM games WHERE game_id = ?", (game_id,))
    if not games:
        return f"Error: Game {game_id} not found."
    target_game = games[0]
    
    if target_game['umpire_id'] is not None:
        return f"Assignment Blocked: Game {game_id} is already assigned to umpire ID {target_game['umpire_id']}. Use 'reassign_umpire_to_game' to override this."
        
    # 5. Check for double booking (same date and time)
    conflicts = database.execute_query(
        "SELECT game_id FROM games WHERE umpire_id = ? AND date = ? AND time = ?",
        (umpire['id'], target_game['date'], target_game['time'])
    )
    if conflicts:
        conflict_id = conflicts[0]['game_id']
        return f"Assignment Blocked: {umpire['name']} is already assigned to Game {conflict_id} at {target_game['date']} {target_game['time']}."
        
    # 6. Perform the update
    database.execute_write("UPDATE games SET umpire_id = ? WHERE game_id = ?", (umpire['id'], game_id))
    return f"Success: {umpire['name']} assigned to Game {game_id}. (Credentials verified){warning_msg}"

def reassign_umpire_to_game(game_id: int, new_umpire_name: str) -> str:
    """Safely overrides an existing assignment to reassign a new umpire to the game."""
    
    # 1. Look up the new umpire ID and credentials
    umpires = database.execute_query("SELECT * FROM umpires WHERE name = ?", (new_umpire_name,))
    if not umpires:
        return f"Error: Umpire '{new_umpire_name}' not found."
    umpire = umpires[0]
    
    # 2. Check if umpire is marked available (Admin Override: Allow but warn)
    warning_msg = ""
    if not umpire['available']:
        warning_msg = f" (Warning: Forced assignment - {umpire['name']} was marked as unavailable)"

    # 3. Validate Credentials
    current_date = datetime.now().strftime("%Y-%m-%d")
    if umpire['registration_expiry'] < current_date:
        return f"Reassignment Blocked: {umpire['name']}'s registration expired on {umpire['registration_expiry']}."
    if umpire['background_check_expiry'] < current_date:
        return f"Reassignment Blocked: {umpire['name']}'s background check expired on {umpire['background_check_expiry']}."
    
    # 4. Check if the game exists (We DELIBERATELY skip the "is already assigned" block here)
    games = database.execute_query("SELECT * FROM games WHERE game_id = ?", (game_id,))
    if not games:
        return f"Error: Game {game_id} not found."
    target_game = games[0]
        
    # 5. Handle Double Bookings implicitly (Seamless Move)
    conflicts = database.execute_query(
        "SELECT game_id FROM games WHERE umpire_id = ? AND date = ? AND time = ? AND game_id != ?",
        (umpire['id'], target_game['date'], target_game['time'], game_id)
    )
    msg_add = ""
    for conflict in conflicts:
        c_id = conflict['game_id']
        database.execute_write("UPDATE games SET umpire_id = NULL WHERE game_id = ?", (c_id,))
        msg_add += f" [Automatically unassigned from conflicting Game {c_id}]"
        
    # 6. Perform the update
    old_umpire = target_game['umpire_id']
    database.execute_write("UPDATE games SET umpire_id = ? WHERE game_id = ?", (umpire['id'], game_id))
    
    msg = f"Success: {umpire['name']} reassigned to Game {game_id}."
    if old_umpire:
        msg += f" (Replaced umpire ID {old_umpire})"
    msg += msg_add + warning_msg
    return msg

def send_sms_to_umpire(umpire_name: str, message: str) -> str:
    """Sends an SMS message to an umpire using their stored phone number (MOCK)."""
    umpires = database.execute_query("SELECT phone_number FROM umpires WHERE name = ?", (umpire_name,))
    if not umpires:
        return f"Error: Umpire '{umpire_name}' not found."
        
    phone = umpires[0]['phone_number']
    
    # MOCK TWILIO INTEGRATION
    print(f"\n[MOCK SMS API] -> Sending to {phone} ({umpire_name}):\n\"{message}\"\n")
    
    return f"Success: SMS sent to {umpire_name} at {phone}."
