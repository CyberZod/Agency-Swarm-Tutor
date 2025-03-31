from agency_swarm import Agent

class UploaderAgent(Agent):
    def __init__(self):
        super().__init__(
            name="UploaderAgent",
            description="Responsible for uploading scraped markdown files to the OpenAI vector store.",
            instructions="./instructions.md", # Points to the instructions file
            tools_folder="./tools", # Will automatically load UploadToOpenAITool.py
            # tools=[UploadToOpenAITool], # Or explicitly list tools
            temperature=0.0, # Low temperature for deterministic tool use
            max_prompt_tokens=25000,
        )

    # def response_validator(self, message):
    #     # Add custom validation logic here if needed
    #     return message
