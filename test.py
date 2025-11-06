# --------------------------------------------------
# Cell 1 & 2: Imports and API Key Configuration
# --------------------------------------------------
import google.generativeai as genai
# This is the corrected import, as per our last discussion
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
import re
import json
import time
import os
from dotenv import load_dotenv

def configure_api(model_name): # We keep this for later
    """
    Loads the API key from .env and configures the Gemini client.
    """
    load_dotenv() 
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    if not GEMINI_API_KEY:
        print("Error: GEMINI_API_KEY not found in .env file.")
        return None
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        print("Gemini API configured successfully.")
        return genai.GenerativeModel(model_name)
    except Exception as e:
        print(f"Error during API configuration: {e}")
        return None

# --------------------------------------------------
# All the helper functions (fetch_transcript, chunk_text, etc.)
# are still here, but they will not be called.
# --------------------------------------------------
def get_video_id(url_or_id):
    regex = r"(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/(?:[^\/\n\s]+\/\S+\/|(?:v|e(?:mbed)?)\/|\S*?[?&]v=)|youtu\.be\/)([a-zA-Z0-9_-]{11})"
    match = re.search(regex, url_or_id)
    if match: return match.group(1)
    elif len(url_or_id) == 11: return url_or_id
    else: raise ValueError(f"Could not extract video ID from: {url_or_id}")

def fetch_transcript(youtube_url_or_id):
    video_id = None
    try:
        video_id = get_video_id(youtube_url_or_id)
        print(f"Extracted Video ID: {video_id}")
        api_instance = YouTubeTranscriptApi()
        fetched_transcript = api_instance.fetch(video_id)
        full_transcript = " ".join([snippet.text for snippet in fetched_transcript.snippets])
        return full_transcript, video_id
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None, None

def chunk_text(text, chunk_size=8000, overlap=400):
    if text is None or not text.strip(): return []
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap
        if start + overlap >= len(text): break
    if start < len(text): chunks.append(text[start:])
    return chunks

def summarize_chunk(chunk, model, attempt=1, max_attempts=3):
    prompt = f"Summarize this chunk: --- {chunk} ---"
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Error summarizing chunk (Attempt {attempt}/{max_attempts}): {e}")
        if attempt < max_attempts:
            time.sleep(2**attempt)
            return summarize_chunk(chunk, model, attempt + 1, max_attempts)
        else:
            return None

def create_final_summary(summaries, model, video_title="this video"):
    combined_summaries = "\n\n".join(summaries)
    prompt = f"""
    Create a formatted summary from these chunks.
    **Overview:**
    [3-4 line overview]
    **Key Takeaways:**
    * [Takeaway 1]
    * [Takeaway 2]
    * [Takeaway 3]
    * [Takeaway 4]
    * [Takeaway 5]
    **Suggested Chapters:**
    * [Chapter 1]
    * [Chapter 2]
    * [Chapter 3]
    ---
    Chunks: {combined_summaries}
    ---
    Final Summary:
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Error creating final summary: {e}")
        return None

def save_summary_to_file(summary_text, video_id, source_url, model_name):
    if not summary_text: return
    try:
        txt_file_name = f"summary_{video_id}.txt"
        with open(txt_file_name, "w", encoding="utf-8") as f: f.write(summary_text)
        print(f"✅ Summary saved to: {txt_file_name}")
        json_file_name = f"summary_{video_id}.json"
        json_output = {"source_url": source_url, "video_id": video_id, "model_used": model_name, "summary_markdown": summary_text}
        with open(json_file_name, "w", encoding="utf-8") as jf: json.dump(json_output, jf, indent=2)
        print(f"✅ JSON version saved to: {json_file_name}")
    except Exception as e: print(f"❌ Error saving summary to file: {e}")

# --------------------------------------------------
# Cell 7: Main Pipeline (DIAGNOSTIC VERSION)
# --------------------------------------------------
def main():
    """
    This is a diagnostic function to list available models.
    """
    # --- DIAGNOSTIC STEP ---
    # Load and configure the API key *without* creating a model yet
    print("Configuring API to list models...")
    load_dotenv() 
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    if not GEMINI_API_KEY:
        print("Error: GEMINI_API_KEY not found in .env file.")
        return
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        print("Gemini API configured successfully.")
    except Exception as e:
        print(f"Error during API configuration: {e}")
        return

    # Now, let's list the available models
    print("\n--- Listing Your Available Models ---")
    print("The script will stop after this. Please paste this list in our chat.")
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(f"  * {m.name}")
        print("---------------------------------")
        return # Stop the script
    except Exception as e:
        print(f"Could not list models: {e}")
        print("This might be an API key or permission issue.")
        return
    # --- END DIAGNOSTIC STEP ---

# This makes the script runnable from the command line
if __name__ == "__main__":
    main()