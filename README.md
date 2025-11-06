# 🎥 YouTube Video Summarizer (Gemini AI)

A simple tool that takes a YouTube video URL, extracts the transcript, and summarizes it using **Google Gemini AI**.

---

## 🛠️ Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/Redoxftw/youtube-summarizer.git
cd youtube-summarizer

### 2. Create a Virtual Environment

This creates an isolated Python environment for your project.

#### 🪟 Windows
```bash
python -m venv .venv
.\.venv\Scripts\activate

#### 🐧 macOS / Linux
```bash
python -m venv .venv
source .venv/bin/activate

### 3. Install Dependencies

Once your virtual environment is activated, install all required packages:

```bash
pip install -r requirements.txt

### 4. Set Up Your API Key

Create a file named `.env` in the root folder of the project and add your **Gemini API key** inside it:

GEMINI_API_KEY=YOUR_API_KEY_HERE


Make sure there are **no quotes** or extra spaces around the key.

## 🚀 How to Run

Once everything is set up, run the main script:

```bash
python main.py

You’ll be asked to paste a YouTube video URL.
After processing, the summarized text will be saved in both .txt and .json files inside the project folder.

[Step 5/5] 🎉 --- FINAL SUMMARY --- 🎉

**Overview:**
A short, engaging summary of the entire video in 3–4 lines.

**Key Takeaways:**
* Key takeaway 1  
* Key takeaway 2  
* Key takeaway 3  
* Key takeaway 4  
* Key takeaway 5  

**Suggested Chapters:**
* Chapter 1 — Topic intro  
* Chapter 2 — Main explanation  
* Chapter 3 — Final insights

## 🧩 Troubleshooting

**1.API key not working?**  
- Make sure your `.env` file is in the **same folder** as `main.py`.  
- The key line should look exactly like this (no quotes or spaces):  

- If you’re still seeing a `404` or `key not found` error, check that your API key is from **Google AI Studio** and that the model name in your code is valid, e.g.:
```python
model="gemini-2.0-flash"

**2. Transcript not loading?** 

Some videos disable captions. Try another one with closed captions enabled.

You can also handle missing transcripts by adding an exception in the code.

💡 Credits

Built by Redox using:

-YouTube Transcript API
-Google Gemini API
-Python 🐍

❤️ Support

If this project helped you, give it a ⭐ on GitHub or share it with a friend learning AI.