# WebsiteQA Agency

Turn AI into an expert on any website with a SINGLE line of code.
==============================================================

Great for understanding documentations!!

Welcome to the **WebsiteQA** agency, a custom AI agency created using the open-source agent orchestration framework, **Agency Swarm**. This agency is designed to automate the process of extracting information from a website and making it available for user queries.

## Agency Structure

The **WebsiteQA** agency is composed of four specialized agents:

- **CEO Agent**: The entry point for user interaction and orchestrator of the agency's workflow.
- **Scraper Agent**: Responsible for scraping content from the target website using its sitemap.
- **Uploader Agent**: Handles uploading the scraped content to an OpenAI vector store.
- **Answering Agent**: Answers user questions based on the content stored in the vector store.

The agency is structured to facilitate a seamless flow from website scraping to content indexing and finally, question answering.

## Installation

To install the required dependencies for this agency, navigate to the `WebsiteQA/` directory and run the following command:

```bash
pip install -r requirements.txt
```

Ensure you have `agency_swarm` installed. You also need to set up the following environment variables, as defined in `.env.exmaple` after renaming it to `.env`:

- `OPENAI_API_KEY`: Your OpenAI API key for accessing OpenAI services.

## Agents

Agents are designed with specific roles to automate the WebsiteQA process:

- **CEO Agent**: Manages the overall workflow, interacts with the user, and delegates tasks to other agents. Receives the website BASE URL e.g `https://example.com` and coordinates the scraping and uploading process.
- **Scraper Agent**: Scrapes website content, focusing on sitemap-based scraping to gather comprehensive data.
- **Uploader Agent**: Uploads scraped content to OpenAI's vector store, making it searchable and ready for question answering.
- **Answering Agent**: Answers user queries based on the information retrieved from the vector store, providing direct answers from the website content.

## Tools

The agents in the WebsiteQA agency utilize a set of tools to perform their tasks effectively. These tools are custom-built within the `agency_swarm` framework and are tailored to each agent's responsibilities. Based on the file structure, these tools might include:

- **Website Scraper Tool**: Used by the ScraperAgent to scrape website content.
- **Upload to OpenAI Tool**: Used by the UploaderAgent to upload content to OpenAI.
- **Built-in FileSearch Tool**: Utilized by the AnsweringAgent to find relevant information within the uploaded documents (vector store).
- **Built-in Code Interpreter Tool**: Used by the AnsweringAgent to write code, creates graphs when necessary.

For detailed information about each agent's tools, refer to the respective agent's directory and tool files (e.g., `WebsiteQA/ScraperAgent/tools/`, `WebsiteQA/UploaderAgent/tools/`, `WebsiteQA/CEO/tools/`, `WebsiteQA/AnsweringAgent/tools/`).

## Usage

### Functionality

The **WebsiteQA** agency provides two main functions callable in `agency.py`:

#### `activate(session_name: str)`

Activates the agency in a `gradio` interface with a new or existing thread, specified by the `session_name : str` argument passed.

Example: `activate("WebsiteQA")`

*   Activates the agency with a new thread named "WebsiteQA".
*   If called again, the thread will be loaded into the agency and the conversation can continue.

#### `deactivate(session_name: str)`

Deletes the thread and all its attributes (vector store, files) from your local directory as well as on OpenAI, specified by the `session_name : str` argument passed.

Example: `deactivate("WebsiteQA")`

*   Deletes the thread(s) associated with "WebsiteQA".

To run the WebsiteQA agency, execute the `agency.py` script located in the `WebsiteQA/` directory:

```bash
python agency.py
```

This command will start the agency, initiating the CEO agent which will then guide you through the process of querying website content. Ensure all environment variables are correctly set before running the agency.

## Files

Here's a brief overview of the files in the `WebsiteQA/` directory:

- `.env`: Contains environment variables required for API keys and other configurations.
- `agency.py`: Main script to instantiate and run the WebsiteQA agency.
- `agency_manifesto.md`: Defines the agency's description, mission, operating environment, and limitations.
- `requirements.txt`: Lists Python dependencies for the agency.
- `thread_functions.py`: Contains functions for managing conversation threads and data persistence.
- `AnsweringAgent/`: Directory containing files for the AnsweringAgent, including its definition, instructions, and tools.
- `CEO/`: Directory containing files for the CEO agent.
- `ScraperAgent/`: Directory containing files for the ScraperAgent.
- `UploaderAgent/`: Directory containing files for the UploaderAgent.
- `__pycache__/`: Python cache directory.

## Conclusion

The **WebsiteQA** agency provides an automated solution for extracting and querying information from websites. By leveraging specialized agents and tools, it streamlines the process of turning website content into an accessible knowledge base. This agency demonstrates the potential of AI-driven automation in information retrieval and question answering, offering a foundation for further development and application in various domains.