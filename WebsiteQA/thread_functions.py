import json
import os
import asyncio
from openai import AsyncOpenAI # Changed from OpenAI
from dotenv import load_dotenv

load_dotenv()

def load_threads(session_name):
    if os.path.exists(f"{session_name}_threads.json"):
        with open(f"{session_name}_threads.json", "r") as file:
            threads = json.load(file)
    else:
        threads = []
    return threads

def save_threads(new_threads, session_name):
    # Save threads to a file or database using the session_name
    with open(f"{session_name}_threads.json", "w") as file:
        json.dump(new_threads, file)


# Use Async Client
client = AsyncOpenAI()

# Helper async function to delete a single file from vector store and then the file object
async def delete_file(async_client, file_id, vector_store_id):
    try:
        # Remove file association from the vector store
        await async_client.vector_stores.files.delete(vector_store_id=vector_store_id, file_id=file_id)
        print(f"Removed file {file_id} from vector store {vector_store_id}.")
        # Attempt to delete the file object itself
        # This might fail if the file is associated with other resources.
        try:
            await async_client.files.delete(file_id)
            print(f"Deleted file object {file_id}.")
        except Exception as e:
            # Log inability to delete file object, might be intentional if shared
            print(f"Could not delete file object {file_id} (may still be associated elsewhere): {e}")
    except Exception as e:
        print(f"Error processing file {file_id} for vector store {vector_store_id}: {e}")
        raise # Re-raise exception to be caught by asyncio.gather

# Helper async function to delete a single thread
async def delete_thread(async_client, thread_id):
    try:
        await async_client.beta.threads.delete(thread_id)
        print(f"Deleted thread {thread_id}.")
    except Exception as e:
        print(f"Error deleting thread {thread_id}: {e}")
        raise # Re-raise exception to be caught by asyncio.gather

async def deactivate_threads(session_name): # Changed to async def
    threads = load_threads(session_name)
    main_thread_id = threads.get("main_thread")
    
    try:
        # Check if main thread has a vector store
        if main_thread_id:
            main_thread = await client.beta.threads.retrieve(main_thread_id) # await added
            if main_thread.tool_resources and main_thread.tool_resources.file_search:
                 vs_ids = main_thread.tool_resources.file_search.vector_store_ids # Plural suggests list
            else:
                 vs_ids = []

            if vs_ids:
                # Assuming we process the first vector store ID if multiple exist
                vector_store_id = vs_ids[0]
                print(f"Processing vector store {vector_store_id} for main thread {main_thread_id}.")

                # Retrieve all files in the vector store asynchronously
                try:
                    vector_store_files = await client.vector_stores.files.list(vector_store_id=vector_store_id) # await added, used vector_store_id

                    # Create tasks to delete each file asynchronously
                    delete_file_tasks = []
                    for file_obj in vector_store_files.data:
                        delete_file_tasks.append(delete_file(client, file_obj.id, vector_store_id))

                    # Run file deletion tasks concurrently
                    if delete_file_tasks:
                        print(f"Attempting to remove/delete {len(delete_file_tasks)} files from vector store {vector_store_id}...")
                        file_results = await asyncio.gather(*delete_file_tasks, return_exceptions=True)
                        # Process results/errors if needed (errors printed in helper)
                        successful_files = sum(1 for r in file_results if not isinstance(r, Exception))
                        print(f"Successfully processed {successful_files} files.")

                    # Delete the vector store itself asynchronously
                    await client.vector_stores.delete(vector_store_id=vector_store_id) # await added, used vector_store_id
                    print(f"Deleted vector store {vector_store_id} for main thread {main_thread_id}.")
                except Exception as e:
                    print(f"Error processing vector store {vector_store_id}: {e}")
            else:
                print(f"No vector stores found for main thread {main_thread_id}.")
        
        # Delete all threads
        thread_ids = []
        for value in threads.values():
            if isinstance(value, dict):
                thread_ids.extend(value.values())
            else:
                thread_ids.append(value)
        # Create tasks to delete each thread asynchronously
        delete_thread_tasks = []
        for thread_id in thread_ids:
            delete_thread_tasks.append(delete_thread(client, thread_id))

        # Run thread deletion tasks concurrently
        if delete_thread_tasks:
            print(f"Attempting to delete {len(delete_thread_tasks)} threads...")
            thread_results = await asyncio.gather(*delete_thread_tasks, return_exceptions=True)
            # Process results/errors if needed (errors printed in helper)
            successful_threads = sum(1 for r in thread_results if not isinstance(r, Exception))
            print(f"Successfully deleted {successful_threads} threads.")
        
        # Delete the threads JSON file
        threads_file = f"{session_name}_threads.json"
        if os.path.exists(threads_file):
            os.remove(threads_file)
            print(f"Deleted threads file {threads_file}.")
        else:
            print(f"Threads file {threads_file} not found.")
        
        print("All threads and associated files deleted successfully.")
    except FileNotFoundError as e:
        print(f"Error: {e}")
            
    except Exception as e:
        print(f"Error processing threads: {e}")
    
# Modified main execution block to run the async deactivate function
async def deactivate(session_name_to_delete):
    print(f"--- Running Deactivation for Session: {session_name_to_delete} ---")
    await deactivate_threads(session_name_to_delete)
    print(f"--- Deactivation Complete for Session: {session_name_to_delete} ---")