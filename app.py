# --------------------------------------------------
# IMPORTS
# --------------------------------------------------
import google.generativeai as genai
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
import re
import json
import time
import streamlit as st  # <-- ADD THIS IMPORT

# --------------------------------------------------
# ALL YOUR HELPER FUNCTIONS (No changes needed)
# --------------------------------------------------

def configure_api(model_name):
    """
    Loads the API key from Streamlit's secrets and configures the Gemini client.
    """
    # Read the API key from Streamlit's secrets
    try:
        GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
    except KeyError:
        st.error("Error: GEMINI_API_KEY not found. Please add it to your Streamlit secrets.")
        return None

    # Configure the Gemini API
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        return genai.GenerativeModel(model_name)
    except Exception as e:
        st.error(f"Error during API configuration: {e}")
        return None

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
        api_instance = YouTubeTranscriptApi()
        fetched_transcript = api_instance.fetch(video_id)
        full_transcript = " ".join([snippet.text for snippet in fetched_transcript.snippets])
        return full_transcript, video_id
    except TranscriptsDisabled:
        st.error(f"Error: Transcripts are disabled for video {video_id}.")
        return None, video_id
    except NoTranscriptFound:
        st.error(f"Error: No transcript found for video {video_id}.")
        return None, video_id
    except Exception as e:
        st.error(f"An unexpected error occurred while fetching transcript: {e}")
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
    """Summarizes a single text chunk using the specified Gemini model."""
    prompt = f"Please provide a concise summary... {chunk} ---" # (Shortened prompt for clarity)
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        if attempt < max_attempts:
            time.sleep(2**attempt)
            return summarize_chunk(chunk, model, attempt + 1, max_attempts)
        else:
            st.error(f"Error summarizing chunk: {e}")
            return None

def create_final_summary(summaries, model, video_title="this video"):
    """Combines all chunk summaries into a final, formatted report."""
    combined_summaries = "\n\n".join(summaries)
    prompt = f"""
    You are an expert video summarizer...
    The output MUST be in the following Markdown format:

    **Overview:**
    [A short, engaging overview of the entire video, 3-4 lines.]

    **Key Takeaways:**
    * [Key takeaway 1]
    ...
    * [Key takeaway 5]

    **Suggested Chapters:**
    * [Chapter Title 1]
    ...
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
        st.error(f"Error creating final summary: {e}")
        return None

# (We are REMOVING the save_summary_to_file function,
# as we will just display the text on the web page.)

# --------------------------------------------------
# ⭐️ STEP 3: THE NEW WEB INTERFACE
# --------------------------------------------------

# Set the title of the web page
st.title("🤖 YouTube Video Summarizer")

# Get the model choice from the user
MODEL_CHOICE = st.selectbox(
    "Choose your model:",
    ("models/gemini-2.5-flash", "models/gemini-pro-latest", "models/gemini-2.5-pro")
)

# Get the YouTube URL from the user
YOUTUBE_URL = st.text_input("Please paste the YouTube URL and press Enter:")

# Create a button that starts the process
if st.button("Generate Summary"):
    if not YOUTUBE_URL:
        st.warning("Please enter a YouTube URL.")
    else:
        # Show a "loading" spinner while it works
        with st.spinner("Generating summary... This may take a moment."):
            try:
                # 1. Configure API
                model = configure_api(MODEL_CHOICE)
                if model:
                    
                    # 2. Fetch Transcript
                    transcript, video_id = fetch_transcript(YOUTUBE_URL)
                    
                    if transcript:
                        # 3. Chunk Text
                        text_chunks = chunk_text(transcript)
                        
                        # 4. Summarize Chunks
                        chunk_summaries = []
                        for i, chunk in enumerate(text_chunks):
                            summary = summarize_chunk(chunk, model)
                            if summary:
                                chunk_summaries.append(summary)
                        
                        # 5. Combine Summaries
                        if chunk_summaries:
                            final_summary = create_final_summary(chunk_summaries, model, video_title=video_id)
                            
                            # 6. Display Final Summary
                            if final_summary:
                                st.success("Summary Generated!")
                                st.markdown(final_summary) # Display as formatted text
                            else:
                                st.error("Could not generate the final summary.")
                        else:
                            st.error("No chunk summaries were generated.")
            except Exception as e:
                st.error(f"An unexpected error occurred: {e}")