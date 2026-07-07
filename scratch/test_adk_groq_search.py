import os
import asyncio
from dotenv import load_dotenv
load_dotenv(".env")

from google.adk.models.lite_llm import LiteLlm
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools.google_search_tool import GoogleSearchTool
from google.adk.tools.tool_context import ToolContext
from google.genai import types

class GroqGoogleSearchTool(GoogleSearchTool):
    def __init__(self):
        super().__init__()
        self.name = "google_search"
        self.description = (
            "Search Google for active job listings or web pages matching the query."
        )

    async def process_llm_request(self, *, tool_context: ToolContext, llm_request) -> None:
        # Bypass the Gemini-only ValueError
        pass

    async def run_async(self, *, args: dict, tool_context: ToolContext) -> str:
        query = args.get("query") or args.get("job_role") or ""
        print(f"Tool Executing Search: {query}")
        return "1. Title: AI Engineer - Scoutit\nLink: https://in.linkedin.com/jobs/view/ai-engineer-at-scoutit\nSnippet: 17 hours ago - As an AI Engineer, you will design, build..."

async def main():
    google_search_tool = GroqGoogleSearchTool()
    
    search_agent = Agent(
        name="linkedin_search_agent",
        model=LiteLlm(model="groq/llama-3.1-8b-instant"),
        instruction="You are an expert search assistant. Use the google_search tool to find LinkedIn job listings.",
        tools=[google_search_tool]
    )
    
    session_service = InMemorySessionService()
    await session_service.create_session(app_name="app", user_id="user", session_id="search_session")
    runner_search = Runner(agent=search_agent, app_name="app", session_service=session_service)
    
    search_prompt = "Search LinkedIn for active entry-level or fresher jobs matching site:linkedin.com \"India\"."
    
    async for event in runner_search.run_async(
        user_id="user", session_id="search_session",
        new_message=types.Content(role="user", parts=[types.Part.from_text(text=search_prompt)]),
    ):
        if event.is_final_response():
            if event.content and event.content.parts:
                print("Final Response:")
                print(event.content.parts[0].text)

if __name__ == "__main__":
    asyncio.run(main())
