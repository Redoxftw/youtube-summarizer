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

def configure_api(model_name):
    """
    Loads the API key from .env and configures the Gemini client.
    """
    # Load environment variables from .env file
    load_dotenv() 
    
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    
    if not GEMINI_API_KEY:
        print("Error: GEMINI_API_KEY not found in .env file.")
        print("Please create a .env file and add: GEMINI_API_KEY=your_key")
        return None

    try:
        genai.configure(api_key=GEMINI_API_KEY)
        print("Gemini API configured successfully.")
        return genai.GenerativeModel(model_name) # Or your model
    except Exception as e:
        print(f"Error during API configuration: {e}")
        return None

# --------------------------------------------------
# Cell 3: Function to Fetch Transcript (CORRECTED)
# --------------------------------------------------
def get_video_id(url_or_id):
    """Extracts the YouTube video ID from a URL or returns the ID if already provided."""
    regex = r"(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/(?:[^\/\n\s]+\/\S+\/|(?:v|e(?:mbed)?)\/|\S*?[?&]v=)|youtu\.be\/)([a-zA-Z0-9_-]{11})"
    match = re.search(regex, url_or_id)
    if match:
        return match.group(1)
    elif len(url_or_id) == 11:
        return url_or_id
    else:
        raise ValueError(f"Could not extract video ID from: {url_or_id}")

def fetch_transcript(youtube_url_or_id):
    """
    Fetches the full transcript for a YouTube video as a single string.
    This version uses the correct .fetch() method.
    """
    video_id = None
    try:
        video_id = get_video_id(youtube_url_or_id)
        print(f"Extracted Video ID: {video_id}")
        
        # --- THIS IS THE CORRECTED CODE ---
        
        # 1. Create an instance of the class
        api_instance = YouTubeTranscriptApi()
        
        # 2. Call .fetch() to get the FetchedTranscript object
        fetched_transcript = api_instance.fetch(video_id)
        
        # 3. Process the new object structure
        # The object contains a .snippets list, and each snippet has a .text attribute
        full_transcript = " ".join([snippet.text for snippet in fetched_transcript.snippets])
        # --- END FIX ---
        
        return full_transcript, video_id
        
    except TranscriptsDisabled:
        print(f"Error: Transcripts are disabled for video {video_id}.")
        return None, video_id
    except NoTranscriptFound:
        print(f"Error: No transcript found for video {video_id}.")
        return None, video_id
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None, None

# --------------------------------------------------
# Cell 4: Function to Chunk Text
# --------------------------------------------------
def chunk_text(text, chunk_size=8000, overlap=400):
    """Splits a long text into smaller, overlapping chunks."""
    if text is None or not text.strip():
        print("Cannot chunk empty or None text.")
        return []
        
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap
        if start + overlap >= len(text):
            break
    if start < len(text):
        chunks.append(text[start:])
    return chunks

# --------------------------------------------------
# Cell 5: Function to Summarize Each Chunk
# --------------------------------------------------
def summarize_chunk(chunk, model, attempt=1, max_attempts=3):
    """Summarizes a single text chunk using the specified Gemini model."""
    prompt = f"""
    Please provide a concise summary of the following video transcript chunk.
    Focus on the main topics, key arguments, and any conclusions.
    Transcript Chunk: --- {chunk} ---
    Concise Summary:
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Error summarizing chunk (Attempt {attempt}/{max_attempts}): {e}")
        if attempt < max_attempts:
            time.sleep(2**attempt)
            return summarize_chunk(chunk, model, attempt + 1, max_attempts)
        else:
            print(f"Failed to summarize chunk after {max_attempts} attempts.")
            return None

# --------------------------------------------------
# Cell 6: Function to Combine Summaries
# --------------------------------------------------
def create_final_summary(summaries, model, video_title="this video"):
    """Combines all chunk summaries into a final, formatted report."""
    combined_summaries = "\n\n".join(summaries)
    prompt = f"""
    You are an expert video summarizer.
    You will be given a series of summaries from sequential chunks of a video transcript titled '{video_title}'.
    Please synthesize these chunked summaries into one cohesive, well-formatted final output.

    The output MUST be in the following Markdown format:

    **Overview:**
    [A short, engaging overview of the entire video, 3-4 lines.]

    **Key Takeaways:**
    * [Key takeaway 1]
    * [Key takeaway 2]
    * [Key takeaway 3]
    * [Key takeaway 4]
    * [Key takeaway 5]

    **Suggested Chapters:**
    * [Chapter Title 1]
    * [Chapter Title 2]
    * [Chapter Title 3]

    ---
    Here are the chunked summaries:
    {combined_summaries}
    ---

    Please generate the final, synthesized summary now.
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Error creating final summary: {e}")
        return None

# --------------------------------------------------
# Cell 8 (Modified): Save Summary Locally
# --------------------------------------------------
def save_summary_to_file(summary_text, video_id, source_url, model_name):
    """Saves the final summary to a .txt and .json file locally."""
    if not summary_text:
        print("No summary text to save.")
        return

    try:
        # Save as .txt
        txt_file_name = f"summary_{video_id}.txt"
        with open(txt_file_name, "w", encoding="utf-8") as f:
            f.write(summary_text)
        print(f"✅ Summary saved to: {txt_file_name}")

        # Save as .json
        json_file_name = f"summary_{video_id}.json"
        json_output = {
            "source_url": source_url,
            "video_id": video_id,
            "model_used": model_name,
            "summary_markdown": summary_text
        }
        with open(json_file_name, "w", encoding="utf-8") as jf:
            json.dump(json_output, jf, indent=2)
        print(f"✅ JSON version saved to: {json_file_name}")

    except Exception as e:
        print(f"❌ Error saving summary to file: {e}")

# --------------------------------------------------
# Cell 7: Main Pipeline
# --------------------------------------------------
def main():
    """
    Main function to run the summarization pipeline.
    """
    # --- User Inputs ---
    YOUTUBE_URL = input("Please paste the YouTube URL and press Enter: ")
    MODEL_CHOICE = "gemini-2.5-flash" # or "gemini-1.5-flash-latest"
    # --- End User Inputs ---

    model = configure_api(MODEL_CHOICE)
    if not model:
        return # Stop if API config failed
    
    # Update model choice in the model object
    # model.model_name = MODEL_CHOICE  <-- DELETE THIS LINE
    print(f"Using model: {MODEL_CHOICE}")

    print(f"\n🚀 Starting the YouTube Video Summarizer for: {YOUTUBE_URL}")

    # 1. Fetch Transcript
    print(f"\n[Step 1/5] Fetching transcript...")
    transcript, video_id = fetch_transcript(YOUTUBE_URL)

    if transcript:
        print(f"✅ Transcript fetched! (Length: {len(transcript)} characters)")
        
        # 2. Chunk Text
        print(f"\n[Step 2/5] Chunking text...")
        text_chunks = chunk_text(transcript)
        print(f"✅ Text divided into {len(text_chunks)} chunks.")
        
        # 3. Summarize Chunks
        chunk_summaries = []
        print(f"\n[Step 3/5] Summarizing chunks...")
        for i, chunk in enumerate(text_chunks):
            print(f"  Summarizing chunk {i+1}/{len(text_chunks)}...")
            summary = summarize_chunk(chunk, model)
            if summary:
                chunk_summaries.append(summary)
            else:
                print(f"  ❌ Failed to summarize chunk {i+1}.")
                
        # 4. Combine Summaries
        if chunk_summaries:
            print(f"\n[Step 4/5] Combining summaries into final report...")
            final_summary = create_final_summary(chunk_summaries, model, video_title=video_id)
            
            # 5. Display Final Summary
            if final_summary:
                print(f"\n[Step 5/5] 🎉 --- FINAL SUMMARY --- 🎉")
                print(final_summary)
                
                # Save the file locally
                save_summary_to_file(final_summary, video_id, YOUTUBE_URL, MODEL_CHOICE)
            else:
                print("\n❌ Error: Could not generate final summary.")
        else:
            print("\n❌ Error: No chunk summaries were generated.")
    else:
        print("\n❌ Stopping pipeline as transcript could not be fetched.")


# This makes the script runnable from the command line
if __name__ == "__main__":
    main()