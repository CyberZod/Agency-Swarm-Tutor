# Agency Manifesto: WebsiteQA

## Agency Description

This agency, named WebsiteQA, is designed to automate the process of extracting information from a website and making it available for user queries. It comprises four specialized agents: CEO, ScraperAgent, UploaderAgent, and AnsweringAgent, working collaboratively to fulfill the user's request.

## Mission Statement

To provide users with an efficient and automated way to query information contained within any given website. We achieve this by scraping the website's content, indexing it into a searchable vector store, and enabling users to ask natural language questions answered directly from the source material.

## Operating Environment

*   **Input:** The agency requires a base URL of the target website provided by the user to the CEO.
*   **Core Process:** It scrapes content using the website's sitemap, converts it to Markdown, uploads these files to an OpenAI vector store associated with the user's session thread, and utilizes the OpenAI Assistants API with the FileSearch tool for answering questions.
*   **Dependencies:**
    *   Requires necessary Python packages as defined in `requirements.txt` (including `agency-swarm`, `openai`, `crawl4ai`, `requests`, `html2text`, `python-dotenv`, `aiofiles`).
    *   Requires the `OPENAI_API_KEY` environment variable to be set for interacting with OpenAI services (Assistants API, File Upload, Vector Stores).
    *   Relies on the `thread_functions.py` module and associated JSON files (e.g., `{session_name}_threads.json`) being correctly implemented and accessible in the environment for managing Assistant threads, as used by the `UploadToOpenAITool`.
    *   Utilizes shared state (`_shared_state`) for internal communication, specifically for passing the list of scraped file paths (`scraped_files`) from ScraperAgent to UploaderAgent, and the session identifier (`session_name`) from CEO to UploaderAgent.
*   **Output:** Answers to user questions, derived solely from the scraped website content, delivered by the AnsweringAgent.
*   **Limitations:** Scraping effectiveness depends on the website structure and the presence/accuracy of a `sitemap.xml`. FileSearch accuracy depends on the quality of scraped content and OpenAI's retrieval capabilities. Assumes the user session and associated OpenAI thread are managed externally or by the framework running the agency.