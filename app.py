import streamlit as st
import requests
import os

# ---- APP TITLE ----
st.set_page_config(page_title="AI Mood Journal", page_icon="📝")
st.title("📝 AI Mood Journal")
st.write(
    "Write about your day and I’ll analyze your mood using AI! "
    "Just type your journal entry below and click 'Analyze Mood'."
)

# ---- INPUT TEXT AREA ----
journal_entry = st.text_area(
    "Write your journal entry here:", 
    height=200
)

# ---- GET API KEY ----
# Option 1: Use environment variable (recommended for deployment)
api_key = os.getenv("GEMINI_API_KEY")
# Option 2: Hardcode (ONLY for testing locally)
# api_key = "YOUR_GEMINI_API_KEY_HERE"

# ---- BUTTON TO ANALYZE ----
if st.button("Analyze Mood"):
    if not journal_entry:
        st.warning("Please write something first!")
    elif not api_key:
        st.error("API key not found! Please set GEMINI_API_KEY in environment variables.")
    else:
        st.info("Analyzing your mood... 🤖")

        # ---- CUSTOM PROMPT FOR AI ----
        # You can change this text to control how the AI responds
        prompt_text = f"""
        Analyze the mood of the following journal entry.
        1. Output only one word for mood: Positive, Neutral, or Negative.
        2. Then provide a short friendly explanation (1-2 sentences).
        Journal Entry: \"\"\"{journal_entry}\"\"\"
        """

        # ---- API REQUEST TO GEMINI ----
        url = "https://gemini.googleapis.com/v1/models/text-bison-001:generate"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        payload = {
            "prompt": prompt_text,
            "max_output_tokens": 150
        }

        try:
            response = requests.post(url, headers=headers, json=payload)
            if response.status_code == 200:
                result = response.json()
                mood_text = result["candidates"][0]["content"]
                st.subheader("Your Mood Analysis:")
                st.write(mood_text)
            else:
                st.error(f"API Error: {response.status_code} {response.text}")
        except Exception as e:
            st.error(f"Request failed: {e}")
