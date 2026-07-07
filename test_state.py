import asyncio
from google.antigravity import Agent, LocalAgentConfig
import os

async def main():
    if "GEMINI_API_KEY" not in os.environ:
        print("MOCK")
        return
    config = LocalAgentConfig()
    agent = Agent(config)
    await agent.__aenter__()
    r1 = await agent.chat("Hi, my name is Kenneth.")
    print("Agent:", await r1.text())
    r2 = await agent.chat("What is my name?")
    print("Agent:", await r2.text())
    await agent.__aexit__(None, None, None)

asyncio.run(main())
