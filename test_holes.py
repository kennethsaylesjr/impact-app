import tools
print("Test 1: Assign valid umpire (John Doe) to Game 1")
print(tools.assign_umpire_to_game(1, "John Doe"))

print("\nTest 2: Assign another umpire (Jane Smith) to Game 1 (Overwrite Protection)")
print(tools.assign_umpire_to_game(1, "Jane Smith"))

print("\nTest 3: Assign John Doe to Game 2 at same time? Wait, Game 1 is 2026-07-10 18:00. Game 2 is 2026-07-11 14:00. Let's create a double booking manually.")
import database
database.execute_write("INSERT INTO games (date, time, location, umpire_id) VALUES ('2026-07-10', '18:00', 'Field Z', NULL)")
games = database.execute_query("SELECT game_id FROM games ORDER BY game_id DESC LIMIT 1")
game4_id = games[0]['game_id']
print(f"Assigning John Doe to Game {game4_id} (Double Booking Protection)")
print(tools.assign_umpire_to_game(game4_id, "John Doe"))

print("\nTest 4: Assign Bob Johnson (Unavailable Protection)")
print(tools.assign_umpire_to_game(2, "Bob Johnson"))

print("\nTest 5: Name Case Sensitivity (jOhN DoE)")
print(tools.assign_umpire_to_game(2, "jOhN DoE"))
