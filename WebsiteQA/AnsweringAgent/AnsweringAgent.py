from agency_swarm import Agent
from agency_swarm.tools import FileSearch # Import the FileSearch tool

class AnsweringAgent(Agent):
    def __init__(self):
        super().__init__(
            name="AnsweringAgent",
            description="Answers user questions based on the website content uploaded to the vector store.",
            instructions="./instructions.md", # Points to the instructions file
            tools=[FileSearch], # Explicitly include the FileSearch tool
            # tools_folder="./tools", # No custom tools in this folder for this agent
            temperature=0.1, # Slightly higher temperature for more natural answers
            max_prompt_tokens=25000,
        )

    # def response_validator(self, message):
    #     # Add custom validation logic here if needed
    #     return message
