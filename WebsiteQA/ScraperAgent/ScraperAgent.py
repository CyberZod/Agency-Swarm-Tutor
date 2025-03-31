from agency_swarm import Agent

class ScraperAgent(Agent):
    def __init__(self):
        super().__init__(
            name="ScraperAgent",
            description="Responsible for scraping website content based on the URL provided by the CEO.",
            instructions="./instructions.md", # Points to the instructions file
            tools_folder="./tools", # Will automatically load WebsiteScraperTool.py
            # tools=[WebsiteScraperTool], # Or explicitly list tools
            temperature=0.0, # Low temperature for deterministic tool use
            max_prompt_tokens=25000,
        )

    # def response_validator(self, message):
    #     # Add custom validation logic here if needed
    #     return message
