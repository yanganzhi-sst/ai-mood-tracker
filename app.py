import streamlit as st
import google.generativeai as genai

# ---- APP TITLE ----
st.set_page_config(page_title="AI Mood Journal", page_icon="📝")
st.title("📝 AI Mood Journal")
st.write(
    "Write about your day and I’ll analyze your mood using AI! "
    "Just type your journal entry below and click 'Analyze Mood'."
)

# ---- INPUT TEXT AREA ----
journal_entry = st.text_area("Write your journal entry here:", height=200)

# ---- API KEY (kept in code) ----
api_key = "PASTE_YOUR_NEW_KEY_HERE"  # <-- keep it here
genai.configure(api_key=api_key)

# ---- LOAD GEMINI MODEL ----
model = genai.GenerativeModel("gemini-1.5-flash")

# ---- SESSION STATE FOR HISTORY ----
if "entries" not in st.session_state:
    st.session_state.entries = []

if "moods" not in st.session_state:
    st.session_state.moods = []

# ---- BUTTON TO ANALYZE ----
if st.button("Analyze Mood"):
    if not journal_entry.strip():
        st.warning("Please write something first!")
    else:
        st.info("Analyzing your mood... 🤖")

        # ---- PROMPT FOR AI ----
        prompt_text = f"""
        Analyze the mood of the following journal entry.
        Output one word only for mood: Positive, Neutral, or Negative.
        Then give a short friendly explanation (1-2 sentences).
        Journal Entry: \"\"\"{journal_entry}\"\"\"
        """

        try:
            response = model.generate_content(prompt_text)
            mood_text = response.text.strip()

            # ---- EXTRACT MOOD WORD ----
            mood_word = "Neutral"
            for word in ["Positive", "Neutral", "Negative"]:
                if word.lower() in mood_text.lower():
                    mood_word = word
                    break

            # ---- DISPLAY WITH COLOR AND EMOJI ----
            if mood_word == "Positive":
                st.success(f"😊 Positive Mood Detected!\n\n{mood_text}")
            elif mood_word == "Neutral":
                st.info(f"😐 Neutral Mood Detected\n\n{mood_text}")
            else:
                st.error(f"😢 Negative Mood Detected\n\n{mood_text}")

            # ---- SAVE TO HISTORY ----
            st.session_state.entries.append(journal_entry)
            st.session_state.moods.append(mood_word)

        except Exception as e:
            st.error(f"AI request failed: {e}")

# ---- DISPLAY HISTORY ----
if st.session_state.entries:
    st.subheader("📖 Journal History")
    for i in range(len(st.session_state.entries) - 1, -1, -1):
        entry = st.session_state.entries[i]
        mood = st.session_state.moods[i]
        if mood == "Positive":
            st.success(f"Entry: {entry}\nMood: 😊 {mood}")
        elif mood == "Neutral":
            st.info(f"Entry: {entry}\nMood: 😐 {mood}")
        else:
            st.error(f"Entry: {entry}\nMood: 😢 {mood}")
