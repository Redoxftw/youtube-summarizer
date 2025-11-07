# 🤖 YouTube Video Summarizer (using Gemini API)

A Python script that fetches the transcript of any YouTube video and uses the Google Gemini API to generate a concise summary with key takeaways and suggested chapters.

This project was built to solve the common problem of getting key information from long videos without having to watch them fully.

---

## ✨ Features
* **Dynamic Input:** Asks the user for a YouTube URL at runtime.  
* **Transcript Fetching:** Automatically pulls the full transcript from any video.  
* **AI Summarization:** Uses `gemini-2.5-flash` (or any compatible Gemini model) to summarize the content.  
* **Structured Output:** Generates a clean, cohesive summary with:
  * A short overview  
  * 5–7 Key Takeaways  
  * 3 Suggested Chapters  
* **File Export:** Saves the final summary to both `.txt` and `.json` files for easy access.


## 🛠️ Setup Instructions

### 1. Clone the Repository
```bash
git clone https://github.com/Redoxftw/youtube-summarizer.git
cd youtube-summarizer
```
### 2. Create a Virtual Environment

This creates an isolated environment for the project.

### Windows
```
python -m venv .venv
.\.venv\Scripts\activate
```

### macOS / Linux
```
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies
```
pip install -r requirements.txt
```


### 4. Set Up Your API Key

Create a file named .env in the root of the project folder and add your Gemini API key:

```GEMINI_API_KEY=YOUR_API_KEY_HERE```

### 🚀 How to Run

Once installed, simply run the main script:

```
python main.py
```

You’ll be prompted to paste a YouTube URL.
After processing, the summary files will be saved in the project folder.

### ✅ Example Output
```
[Step 5/5] 🎉 --- FINAL SUMMARY --- 🎉

Overview:
A short, engaging overview of the entire video, 3–4 lines.

Key Takeaways:
* Key takeaway 1  
* Key takeaway 2  
* Key takeaway 3  
* Key takeaway 4  
* Key takeaway 5  

Suggested Chapters:
* Chapter Title 1  
* Chapter Title 2  
* Chapter Title 3
```

### 💡 Notes

If you get an API key error, make sure your .env file is in the same folder as main.py.

Ensure your Gemini API key is from Google AI Studio and that billing is enabled (if required).

To deactivate the virtual environment:
```
deactivate
```
### 🧠 Built With

- Python 3.9+
- google-generativeai
- youtube-transcript-api
- dotenv

### 🧍‍♂️ Author

Vishwash Agarwal

📍 VIT Bhopal University

🎓 Integrated M.Tech in Data Science
