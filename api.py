from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from contextlib import asynccontextmanager
import database
import os

# Global agent instance
global_agent = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global global_agent
    try:
        from google.antigravity import Agent, LocalAgentConfig, types
        from tools import get_unassigned_games, get_available_umpires, assign_umpire_to_game, reassign_umpire_to_game, check_credentials, send_sms_to_umpire
        
        config = LocalAgentConfig(
            capabilities=types.CapabilitiesConfig(enable_subagents=True),
            tools=[get_unassigned_games, get_available_umpires, assign_umpire_to_game, reassign_umpire_to_game, check_credentials, send_sms_to_umpire],
            system_instruction=(
                "You are the Manager Agent for an umpiring business. "
                "You have tools connected to a live SQLite database. "
                "You can send SMS messages using the send_sms_to_umpire tool."
            )
        )
        # Initialize and enter the agent context so it persists memory across API calls
        global_agent = Agent(config)
        await global_agent.__aenter__()
        
        # Load rulebook if it exists
        from google.antigravity.types import Document
        if os.path.exists("rulebook.pdf"):
            rulebook = Document.from_file("rulebook.pdf")
            await global_agent.chat(["This is the official USSSA Fastpitch Rulebook. Keep this in your context.", rulebook])
            
        yield
        
        # Cleanup
        await global_agent.__aexit__(None, None, None)
    except ImportError:
        print("WARNING: google-antigravity not found. API will run in Mock Mode.")
        yield

app = FastAPI(lifespan=lifespan)

class ChatRequest(BaseModel):
    message: str

class ReassignRequest(BaseModel):
    game_id: int
    umpire_name: str

class LoginRequest(BaseModel):
    name: str
    password: str

class ToggleAvailabilityRequest(BaseModel):
    umpire_id: int
    available: bool

class UmpireImport(BaseModel):
    name: str
    phone_number: str
    level: str
    pay_rate: float
    registration_expiry: str
    background_check_expiry: str

class ImportRosterRequest(BaseModel):
    umpires: list[UmpireImport]

class GameImport(BaseModel):
    date: str
    time: str
    location: str

class ImportGamesRequest(BaseModel):
    games: list[GameImport]

class ReportScoreRequest(BaseModel):
    game_id: int
    status: str
    score: str

class MassRainoutRequest(BaseModel):
    location: str
    date: str = None

async def get_agent_response(msg: str) -> str:
    global global_agent
    if global_agent is not None:
        if "GEMINI_API_KEY" not in os.environ:
            return "Error: GEMINI_API_KEY is not set."
        response = await global_agent.chat(msg)
        return await response.text()
    else:
        return f"[MOCK AGENT]: I received your message: '{msg}'. Since the Antigravity SDK is not installed in this environment, I am responding in mock mode."

@app.get("/api/umpires")
def get_umpires():
    return database.execute_query("SELECT * FROM umpires")

@app.get("/api/games")
def get_games():
    return database.execute_query("SELECT * FROM games")

@app.post("/api/chat")
async def chat(req: ChatRequest):
    reply = await get_agent_response(req.message)
    return {"reply": reply}

@app.post("/api/reassign")
def api_reassign(req: ReassignRequest):
    from tools import reassign_umpire_to_game
    result = reassign_umpire_to_game(req.game_id, req.umpire_name)
    if result.startswith("Success"):
        return {"success": True, "message": result}
    return {"success": False, "message": result}

@app.post("/api/login")
def login(req: LoginRequest):
    if req.name.lower() == "admin" and req.password == "admin":
        return {"success": True, "role": "admin", "umpire_id": None}
    
    hashed_pw = database.hash_password(req.password)
    umpires = database.execute_query("SELECT id FROM umpires WHERE name = ? AND password_hash = ?", (req.name, hashed_pw))
    if umpires:
        return {"success": True, "role": "umpire", "umpire_id": umpires[0]['id']}
    
    return {"success": False, "message": "Invalid credentials"}

@app.post("/api/toggle_availability")
def toggle_availability(req: ToggleAvailabilityRequest):
    database.execute_write("UPDATE umpires SET available = ? WHERE id = ?", (req.available, req.umpire_id))
    return {"success": True}

@app.post("/api/import_roster")
def import_roster(req: ImportRosterRequest):
    default_pw = database.hash_password("umpire123")
    inserted_count = 0
    errors = []
    
    for u in req.umpires:
        try:
            database.execute_write('''
                INSERT INTO umpires (name, phone_number, password_hash, available, level, pay_rate, registration_expiry, background_check_expiry) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (u.name, u.phone_number, default_pw, True, u.level, u.pay_rate, u.registration_expiry, u.background_check_expiry))
            inserted_count += 1
        except Exception as e:
            errors.append(f"Failed to import {u.name}: {str(e)}")
            
    return {"success": len(errors) == 0, "inserted": inserted_count, "errors": errors}

@app.post("/api/import_games")
def import_games(req: ImportGamesRequest):
    inserted_count = 0
    errors = []
    
    for g in req.games:
        try:
            database.execute_write('''
                INSERT INTO games (date, time, location, status) 
                VALUES (?, ?, ?, 'Scheduled')
            ''', (g.date, g.time, g.location))
            inserted_count += 1
        except Exception as e:
            errors.append(f"Failed to import game at {g.location}: {str(e)}")
            
    return {"success": len(errors) == 0, "inserted": inserted_count, "errors": errors}

@app.post("/api/report_score")
def report_score(req: ReportScoreRequest):
    database.execute_write("UPDATE games SET status = ?, score = ? WHERE game_id = ?", (req.status, req.score, req.game_id))
    return {"success": True}

@app.post("/api/mass_rainout")
def mass_rainout(req: MassRainoutRequest):
    # Only cancel games that are not already Completed or Forfeited
    updated = database.execute_write(
        "UPDATE games SET status = 'Rained Out' WHERE location = ? AND date = ? AND status = 'Scheduled'", 
        (req.location, req.date)
    )
    return {"success": True, "updated": updated}

# Serve static frontend
app.mount("/static", StaticFiles(directory="frontend"), name="static")

@app.get("/")
def read_root():
    return FileResponse("frontend/index.html")
