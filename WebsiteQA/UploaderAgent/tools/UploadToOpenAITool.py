import asyncio
from typing import List
from openai import AsyncOpenAI
from pathlib import Path
import aiofiles
from agency_swarm.tools import BaseTool
from WebsiteQA.thread_functions import load_threads # Assuming thread_functions.py is accessible
import os
from dotenv import load_dotenv
from pydantic import Field

load_dotenv()

client = AsyncOpenAI()

class UploadToOpenAITool(BaseTool):
    """
    Async implementation for uploading files to OpenAI with vector store management.
    Handles concurrent uploads and automatic vector store association.
    Retrieves scraped file paths from shared state ('scraped_files') and requires
    'session_name' to be set in shared state to identify the correct thread.
    """
    async def run(self) -> str:
        """Main async entry point for the upload workflow."""
        # ✅ Retrieve session ID
        if not (session_name := self._shared_state.get("session_name")):
            return "Error: session ID (session_name) not found in shared state. Cannot determine target thread."

        # ✅ Retrieve saved file paths
        file_paths = self._shared_state.get("scraped_files", [])
        if not file_paths:
            # Check if the key exists but is empty, or doesn't exist
            if self._shared_state.get("scraped_files") is None:
                 return f"Error: 'scraped_files' key not found in shared state for session {session_name}."
            else:
                 return f"Error: No files available in 'scraped_files' for session {session_name}."


        # ✅ Retrieve the correct thread ID using session_name
        # Ensure thread_functions.py and the JSON file are in the correct location
        try:
            threads = load_threads(session_name)
            main_thread_id = threads.get("main_thread")
            if not main_thread_id:
                return f"Error: No main thread found for session '{session_name}' in threads file."
        except FileNotFoundError:
             return f"Error: Could not find the threads JSON file for session '{session_name}'. Make sure thread_functions.py is configured correctly."
        except Exception as e:
             return f"Error loading threads for session '{session_name}': {str(e)}"


        try:
            # ✅ Handle vector store lifecycle
            vs_id = await self._manage_vector_store(main_thread_id, session_name)

            # ✅ Concurrently upload all files
            file_ids = await self._process_files(file_paths)

            # ✅ Attach files to vector store
            await self._attach_files_to_store(vs_id, file_ids)

            # Clear the scraped files from shared state after successful upload
            self._shared_state.set("scraped_files", [])

            return f"✅ Successfully uploaded {len(file_ids)} files. Thread: {main_thread_id}, Vector Store: {vs_id}"

        except Exception as e:
            return f"❌ Critical error during upload/attachment: {str(e)}"

    async def _manage_vector_store(self, thread_id: str, session_name: str) -> str:
        """Handle vector store lifecycle for a thread."""
        try:
            # Retrieve thread details
            thread = await client.beta.threads.retrieve(thread_id)

            # ✅ Reuse existing vector store if available
            if existing := self._get_existing_vector_store(thread):
                print(f"Found existing vector store {existing} for thread {thread_id}")
                return existing

            # ✅ Otherwise, create a new vector store
            print(f"Creating new vector store for thread {thread_id}")
            return await self._create_vector_store(thread_id, session_name)

        except Exception as e:
            raise RuntimeError(f"Vector store management failed for thread {thread_id}: {str(e)}")

    def _get_existing_vector_store(self, thread) -> str | None:
        """Extract existing vector store ID from thread object."""
        try:
            return (
                thread.tool_resources.file_search.vector_store_ids[0]
                if (thread.tool_resources and thread.tool_resources.file_search and thread.tool_resources.file_search.vector_store_ids)
                else None
            )
        except Exception as e:
            print(f"Error accessing tool_resources for vector store ID: {e}")
            return None


    async def _create_vector_store(self, thread_id: str, session_name: str) -> str:
        """Create and attach a new vector store to the thread."""
        vs = await client.vector_stores.create(
            name=f"vs_{session_name}",
            # expires_after={'anchor': 'last_active_at', 'days': 7} # Example expiration
        )
        print(f"Created vector store {vs.id} for session {session_name}")

        await client.beta.threads.update(
            thread_id=thread_id,
            tool_resources={"file_search": {"vector_store_ids": [vs.id]}}
        )
        print(f"Attached vector store {vs.id} to thread {thread_id}")
        return vs.id

    async def _process_files(self, paths: List[str]) -> List[str]:
        """Orchestrate concurrent file uploads."""
        print(f"Starting upload for {len(paths)} files...")
        results = await asyncio.gather(
            *[self._upload_file(p) for p in paths],
            return_exceptions=True
        )

        # ✅ Filter out failures and log them
        successful = []
        failed_count = 0
        for result, path in zip(results, paths):
            if isinstance(result, Exception):
                print(f"⚠️ Failed to upload {Path(path).name}: {str(result)}")
                failed_count += 1
            elif result: # Ensure result is not None
                successful.append(result.id)
                print(f"Successfully uploaded {Path(path).name} as file ID {result.id}")


        if not successful:
            raise RuntimeError("❌ All file uploads failed.")
        if failed_count > 0:
             print(f"⚠️ Warning: {failed_count} file(s) failed to upload.")


        return successful

    async def _upload_file(self, path: str, retries: int = 3):
        """Single file upload handler with retry logic and filename preservation."""
        filename = Path(path).name # Extract filename with extension

        if not os.path.exists(path):
             raise FileNotFoundError(f"File not found at path: {path}")


        for attempt in range(retries):
            try:
                async with aiofiles.open(path, "rb") as f:
                    file_content = await f.read()
                    # Pass filename with extension as part of the file tuple
                    print(f"Attempting to upload {filename} (Attempt {attempt + 1}/{retries})...")
                    file = await client.files.create(
                        file=(filename, file_content), # Include filename in upload
                        purpose="assistants"
                    )
                    print(f"File {filename} uploaded successfully with ID: {file.id}. Deleting local file...")
                    # After successful upload, delete the file from local storage
                    try:
                        await aiofiles.os.remove(path)
                        print(f"Local file {filename} deleted.")
                    except Exception as delete_error:
                         print(f"⚠️ Warning: Failed to delete local file {filename}: {delete_error}")

                    return file # Return the file object on success
            except Exception as e:
                print(f"⚠️ Error uploading {filename} (Attempt {attempt + 1}/{retries}): {e}")
                if attempt < retries - 1:
                    await asyncio.sleep(2 ** attempt) # Exponential backoff
                else:
                    # Raise the error only after all retries fail
                    raise RuntimeError(f"❌ File upload failed for {filename} after {retries} attempts: {str(e)}")


    async def _attach_files_to_store(self, vs_id: str, file_ids: List[str]):
        """Batch attach files to vector store."""
        if not file_ids:
             print("No file IDs to attach.")
             return

        print(f"Attaching {len(file_ids)} files to vector store {vs_id}...")
        try:
            # Use file batching for potentially better performance/reliability
            batch = await client.vector_stores.file_batches.create_and_poll(
                 vector_store_id=vs_id,
                 file_ids=file_ids
            )

            # Check batch status (optional but good practice)
            if batch.status == 'completed':
                print(f"Successfully attached {batch.file_counts.completed} files to vector store {vs_id}.")
            else:
                 print(f"⚠️ File batch status: {batch.status}. Files completed: {batch.file_counts.completed}, Failed: {batch.file_counts.failed}")
                 if batch.file_counts.failed > 0:
                      # Potentially list failed files if API provides details
                      raise RuntimeError(f"Attachment failed for {batch.file_counts.failed} file(s).")


        except Exception as e:
            raise RuntimeError(f"Attachment to vector store {vs_id} failed: {str(e)}")

# Example Test Case (requires async execution and shared state setup)
if __name__ == "__main__":
    async def main():
        # --- Setup for Testing ---
        # 1. Create dummy files to upload
        test_dir = "test_upload_files"
        os.makedirs(test_dir, exist_ok=True)
        test_files = []
        for i in range(2):
            fpath = os.path.join(test_dir, f"test_file_{i}.md")
            with open(fpath, "w") as f:
                f.write(f"Content for test file {i}")
            test_files.append(fpath)

        # 2. Mock shared state (replace with actual shared state mechanism if needed)
        class MockSharedState:
            def __init__(self):
                self._state = {}
            def set(self, key, value):
                self._state[key] = value
                print(f"MockSharedState: Set {key} = {value}")
            def get(self, key, default=None):
                value = self._state.get(key, default)
                print(f"MockSharedState: Get {key} -> {value}")
                return value

        mock_state = MockSharedState()
        mock_state.set("scraped_files", test_files)
        # IMPORTANT: Replace with a REAL session name and ensure a corresponding thread exists in OpenAI
        mock_state.set("session_name", "test_session_123")
        # Ensure 'thread_functions.py' and a corresponding 'test_session_123_threads.json'
        # file (with a 'main_thread' ID) exist and are accessible.

        # 3. Create tool instance with mocked state
        tool = UploadToOpenAITool()
        tool._shared_state = mock_state # Inject mock state

        # --- Run the tool ---
        print("--- Running UploadToOpenAITool ---")
        result = await tool.run()
        print("--- Tool Run Result ---")
        print(result)

        # --- Cleanup ---
        # import shutil
        # shutil.rmtree(test_dir) # Clean up dummy files
        print(f"Cleanup: Remember to manually remove '{test_dir}' and potentially the vector store created in OpenAI.")


    # Requires OPENAI_API_KEY environment variable
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY environment variable not set.")
    else:
        try:
            asyncio.run(main())
        except Exception as e:
            print(f"Error running test: {e}")