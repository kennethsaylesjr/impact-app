import asyncio
import os
from google.antigravity import Agent, LocalAgentConfig, types
from google.antigravity.types import Document
from tools import get_unassigned_games, get_available_umpires, assign_umpire_to_game, check_credentials

async def main():
    if "GEMINI_API_KEY" not in os.environ:
        print("Please set your GEMINI_API_KEY environment variable.")
        return

    # The Manager Agent uses enable_subagents=True to dynamically spawn
    # the Scheduler, Rules Expert, and Certification subagents as needed.
    config = LocalAgentConfig(
        capabilities=types.CapabilitiesConfig(
            enable_subagents=True,
        ),
        tools=[
            get_unassigned_games,
            get_available_umpires,
            assign_umpire_to_game,
            check_credentials
        ],
        system_instruction=(
            "You are the Manager Agent for an umpiring business. "
            "You have tools connected to a live SQLite database to check schedules, umpires, and credentials. "
            "If a user asks to perform complex scheduling logic, spawn a 'Scheduler Sub-agent' to figure it out, then use your tools to assign the umpire. "
            "If a user asks a complex rules question, spawn a 'Rules Expert Sub-agent' to answer it (passing the rulebook to it). "
            "If a user asks about an umpire's background check or registration status, spawn a 'Certification Sub-agent' to use the check_credentials tool and report back. "
            "IMPORTANT: Your assign_umpire_to_game tool now has strict internal validation and will block assignments for umpires with expired credentials. If this happens, report the expiration date to the user."
        )
    )

    print("Starting Umpire Team Manager Agent (Phase 3: Certification Integration)...")
    async with Agent(config) as agent:
        # Pre-load the rulebook into the agent's context
        if os.path.exists("rulebook.pdf"):
            print("Loading official rulebook...")
            rulebook = Document.from_file("rulebook.pdf")
            await agent.chat(["This is the official USSSA Fastpitch Rulebook. Keep this in your context so your Rules Expert Sub-agent can use it to answer rules questions.", rulebook])
            print("Rulebook loaded successfully!\n")

        print("Agent ready! Type 'exit' to quit.\n")
        
        while True:
            user_input = input("You: ")
            if user_input.lower() in ['exit', 'quit']:
                break
                
            try:
                response = await agent.chat(user_input)
                print(f"\nManager Agent: {await response.text()}\n")
            except Exception as e:
                print(f"\nError: {e}\n")

if __name__ == "__main__":
    asyncio.run(main())
