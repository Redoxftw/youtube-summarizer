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
@st.cache_data
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
@st.cache_data
def summarize_chunk(chunk, model_name, attempt=1, max_attempts=3):
    """Summarizes a single text chunk using the specified Gemini model."""
    prompt = f"Please provide a concise summary... {chunk} ---" # (Shortened prompt for clarity)
    try:
        # Create the model inside the cached function
        model = configure_api(model_name)
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        if attempt < max_attempts:
            time.sleep(2**attempt)
            return summarize_chunk(chunk, model, attempt + 1, max_attempts)
        else:
            st.error(f"Error summarizing chunk: {e}")
            return None
@st.cache_data
def create_final_summary(summaries, model_name, summary_format, video_title="this video"):
    """Combines all chunk summaries into a final, formatted report."""
    
    combined_summaries = "\n\n".join(summaries)
    
    prompt = f"""
    You are an expert video summarizer.
    You will be given a series of summaries from sequential chunks of a video transcript titled '{video_title}'.
    Please synthesize these chunked summaries into one cohesive, well-formatted final output.

    The user has requested the output in this specific format: **{summary_format}**

    ---
    Here are the chunked summaries:
    {combined_summaries}
    ---

    Please generate the final, synthesized summary now.

    **IMPORTANT FORMATTING RULES:**
    - If the user requested "Standard Summary", you MUST provide:
      **Overview:** [A short, engaging overview...]
      **Key Takeaways:** [5-7 bullet points...]
      **Suggested Chapters:** [3-5 chapter titles...]
    - If the user requested "Bullet-Point Takeaways", provide *only* a list of 10-15 detailed bullet points.
    - If the user requested "Tweet Thread (3 Tweets)", provide exactly 3 numbered tweets (1/3, 2/3, 3/3) that are concise and engaging.
    - If the user requested "Blog Post", provide a short, 3-paragraph blog post based on the content.
    """
    
    try:
        # This is the new, clean way:
        model = configure_api(model_name)
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

# Get the summary format from the user
summary_format = st.radio(
    "Select your desired summary format:",
    ("Standard Summary", "Bullet-Point Takeaways", "Tweet Thread (3 Tweets)", "Blog Post"),
    key="format_choice",
    horizontal=True
)

# Get the YouTube URL from the user
YOUTUBE_URL = st.text_input("Please paste the YouTube URL and press Enter:")

# --- 1. GENERATE DATA BLOCK ---
# This block only runs when the button is clicked.
# Its only job is to create data and save it to st.session_state.

if st.button("Generate Summary"):
    if not YOUTUBE_URL:
        st.warning("Please enter a YouTube URL.")
    else:
        # Clear any old results before we start a new job
        st.session_state.pop("final_summary", None)
        st.session_state.pop("full_transcript", None)
        st.session_state.pop("video_id", None)
        
        with st.spinner("Generating summary... This may take a moment."):
            try:
                # 1. Fetch Transcript
                transcript, video_id = fetch_transcript(YOUTUBE_URL)
                
                if transcript:
                    st.session_state["full_transcript"] = transcript # Save transcript
                    
                    # 2. Chunk Text
                    text_chunks = chunk_text(transcript)
                    
                    # 3. Summarize Chunks
                    chunk_summaries = []
                    for i, chunk in enumerate(text_chunks):
                        summary = summarize_chunk(chunk, MODEL_CHOICE)
                        if summary:
                            chunk_summaries.append(summary)
                    
                    # 4. Combine Summaries
                    if chunk_summaries:
                        final_summary = create_final_summary(chunk_summaries, MODEL_CHOICE, summary_format, video_title=video_id)
                        
                        if final_summary:
                            # 5. Save results to session state
                            st.session_state["final_summary"] = final_summary
                            st.session_state["video_id"] = video_id
                        else:
                            st.error("Could not generate the final summary.")
                    else:
                        st.error("No chunk summaries were generated.")
            except Exception as e:
                st.error(f"An unexpected error occurred: {e}")

# --- 2. DISPLAY DATA BLOCK ---
# This block runs every time the app re-runs (e.g., when you type).
# It just reads data from st.session_state and displays it.

if "final_summary" in st.session_state:
    st.success("Summary Generated!")
    st.markdown(st.session_state["final_summary"])
    
    st.download_button(
        label="Download Summary as .txt",
        data=st.session_state["final_summary"],
        file_name=f"summary_{st.session_state['video_id']}.txt",
        mime="text/plain"
    )
    
    # Show the Q&A box
    if "full_transcript" in st.session_state:
        st.markdown("---")
        st.subheader("💬 Chat with the Video")
        User_question = st.text_input("Ask a follow-up question about this video:")
        
        if User_question:
            with st.spinner("Finding the answer..."):
                prompt = f"""
                Here is the full transcript of a video:
                ---
                {st.session_state["full_transcript"]}
                ---
                Using ONLY this transcript, please answer the following question:
                {User_question}
                If the answer is not in the transcript, say "I'm sorry, that information is not in the video transcript."
                """
                
                model = configure_api(MODEL_CHOICE) # We can use MODEL_CHOICE from the top
                response = model.generate_content(prompt)
                st.markdown(response.text)