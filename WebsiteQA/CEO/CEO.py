from agency_swarm import Agent

class CEO(Agent):
    def __init__(self):
        super().__init__(
            name="CEO",
            description="Manages the workflow, communicates with the user and other agents. Receives the website URL and coordinates the scraping and uploading process.",
            instructions="./instructions.md", # Points to the instructions file
            # tools=[], # No specific tools needed for CEO in this flow initially
            tools_folder="./tools", # Standard practice to include, even if empty initially
            temperature=0.3,
            max_prompt_tokens=25000,
        )

    # Override the response_validator to potentially handle specific responses or state changes
    # def response_validator(self, message):
    #     # Add custom validation logic here if needed
    #     return message
