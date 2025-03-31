from agency_swarm import Agency
from agency_swarm.tools.send_message import SendMessageAsyncThreading
from CEO import CEO
from ScraperAgent import ScraperAgent
from UploaderAgent import UploaderAgent
from AnsweringAgent import AnsweringAgent
from thread_functions import load_threads, save_threads
from dotenv import load_dotenv
import asyncio
import os

load_dotenv()
# Assuming thread_functions.py is accessible in the environment or added to PYTHONPATH
# If UploadToOpenAITool relies on it, ensure it's available.

# Instantiate agents
ceo = CEO()
scraper_agent = ScraperAgent()
uploader_agent = UploaderAgent()
answering_agent = AnsweringAgent()

# Define the agency structure and communication flow

class WebQAAgency(Agency):
    def __init__(self, session_name):
        self.session_name = session_name
        super().__init__(
            [
                ceo, answering_agent, # CEO is the entry point for user interaction
                [ceo, scraper_agent],      # CEO can instruct ScraperAgent
                [scraper_agent, ceo],      # ScraperAgent can report back to CEO
                [ceo, uploader_agent],     # CEO can instruct UploaderAgent
                [uploader_agent, ceo],     # UploaderAgent can report back to CEO
                [ceo, answering_agent],    # CEO can direct the user to AnsweringAgent (and potentially interact if needed)
                # User can interact with AnsweringAgent after CEO directs them, handled by the framework.
            ],
            shared_instructions='agency_manifesto.md',
            threads_callbacks={
                'load': lambda: load_threads(session_name=session_name),
                'save': lambda new_threads: save_threads(new_threads, session_name=session_name)
            },
            send_message_tool_class=SendMessageAsyncThreading,
            max_prompt_tokens=25000, # Default max tokens for conversation history
            temperature=0.2, # Default temperature for agents (can be overridden in agent definition)
        )

async def activate(session_name):
    agency = WebQAAgency(session_name=session_name)
    agency.shared_state.set('session_name', session_name)
    agency.demo_gradio()

if __name__ == '__main__':
    asyncio.run(activate("Pydantic AI"))