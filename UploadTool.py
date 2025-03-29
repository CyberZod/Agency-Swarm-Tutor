import asyncio
from typing import List
from openai import AsyncOpenAI
from pathlib import Path
import aiofiles
from agency_swarm.tools import BaseTool
from thread_functions import load_threads
import os
from dotenv import load_dotenv
from pydantic import Field

load_dotenv()

client = AsyncOpenAI()

class UploadToOpenAITool(BaseTool):
    """
    Async implementation for uploading files to OpenAI with vector store management.
    Handles concurrent uploads and automatic vector store association.
    """

    def __init__(self):
        """Initialize the OpenAI async client."""
        super().__init__()  # Use private variable to avoid Pydantic validation
        UploadToOpenAITool._shared_state = {
            "session_name": "First_Rag",
            "scraped_files": ["./test1.md", "./test2.md"]  # Replace with actual file paths
        }

    async def run(self) -> str:
        """Main async entry point for the upload workflow."""
        # ✅ Retrieve session ID
        if not (session_name := self._shared_state.get("session_name")):
            return "Error: session ID not found in shared state."

        # ✅ Retrieve saved file paths
        file_paths = self._shared_state.get("scraped_files", [])
        if not file_paths:
            return f"Error: No files available for session {session_name}."

        # ✅ Retrieve the correct thread ID
        threads = load_threads(session_name)
        main_thread_id = threads.get("main_thread")
        if not main_thread_id:
            return f"Error: No main thread found for session '{session_name}'."

        try:
            # ✅ Handle vector store lifecycle
            vs_id = await self._manage_vector_store(main_thread_id, session_name)

            # ✅ Concurrently upload all files
            file_ids = await self._process_files(file_paths)

            # ✅ Attach files to vector store
            await self._attach_files_to_store(vs_id, file_ids)

            return f"✅ Successfully uploaded {len(file_ids)} files. Thread: {main_thread_id}, Vector Store: {vs_id}"

        except Exception as e:
            return f"❌ Critical error: {str(e)}"

    async def _manage_vector_store(self, thread_id: str, session_name: str) -> str:
        """Handle vector store lifecycle for a thread."""
        try:
            # Retrieve thread details
            thread = await client.beta.threads.retrieve(thread_id)

            # ✅ Reuse existing vector store if available
            if existing := self._get_existing_vector_store(thread):
                return existing

            # ✅ Otherwise, create a new vector store
            return await self._create_vector_store(thread_id, session_name)

        except Exception as e:
            raise RuntimeError(f"Vector store management failed: {str(e)}")

    def _get_existing_vector_store(self, thread) -> str | None:
        """Extract existing vector store ID from thread object."""
        return (
            thread.tool_resources.file_search.vector_store_ids[0]
            if (thread.tool_resources and thread.tool_resources.file_search and thread.tool_resources.file_search.vector_store_ids)
            else None
        )

    async def _create_vector_store(self, thread_id: str, session_name: str) -> str:
        """Create and attach a new vector store to the thread."""
        vs = await client.vector_stores.create(
            name=f"vs_{session_name}",
            expires_after=None # 1 week expiration
        )

        await client.beta.threads.update(
            thread_id=thread_id,
            tool_resources={"file_search": {"vector_store_ids": [vs.id]}}
        )
        return vs.id

    async def _process_files(self, paths: List[str]) -> List[str]:
        """Orchestrate concurrent file uploads."""
        results = await asyncio.gather(
            *[self._upload_file(p) for p in paths],
            return_exceptions=True
        )

        # ✅ Filter out failures and log them
        successful = []
        for result, path in zip(results, paths):
            if isinstance(result, Exception):
                print(f"⚠️ Failed to upload {Path(path).name}: {str(result)}")
            else:
                successful.append(result.id)

        if not successful:
            raise RuntimeError("❌ All file uploads failed.")

        return successful

    async def _upload_file(self, path: str, retries: int = 3):
        """Single file upload handler with retry logic and filename preservation."""
        filename = Path(path).name  # Extract filename with extension
        
        for attempt in range(retries):
            try:
                async with aiofiles.open(path, "rb") as f:
                    file_content = await f.read()
                    # Pass filename with extension as part of the file tuple
                    return await client.files.create(
                        file=(filename, file_content),  # Include filename in upload
                        purpose="assistants"
                    )
            except Exception as e:
                if attempt < retries - 1:
                    print(f"⚠️ Retry {attempt + 1}/{retries} for {filename} due to error: {e}")
                    await asyncio.sleep(2)
                else:
                    raise RuntimeError(f"❌ File upload failed: {str(e)}")
            
    async def _attach_files_to_store(self, vs_id: str, file_ids: List[str]):
        """Batch attach files to vector store."""
        try:
            await client.vector_stores.file_batches.create(
                vector_store_id=vs_id,
                file_ids=file_ids
            )
        except Exception as e:
            raise RuntimeError(f"Attachment failed: {str(e)}")
