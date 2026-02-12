# app.py
# MindEase: Mood Journal + AI Mood Analyzer + Mood History + Self-care Tools + Crisis Support
# Streamlit Cloud friendly (no ngrok, no login)

import os
from datetime import datetime, date

import pandas as pd
import streamlit as st
import google.generativeai as genai

# ---------- CONFIGURATION ----------
st.set_page_config(page_title="MindEase", layout="centered", page_icon="🌱")

DATA_FILE = "mood_log.csv"

# Gemini API Key - REPLACE WITH YOUR KEY
GEMINI_API_KEY = "AIzaSyD5xvU9HFoT3XpogoAoJ3EGR-v35AEbo_Y"
genai.configure(api_key=GEMINI_API_KEY)
GEMINI_MODEL = genai.GenerativeModel("gemini-2.5-flash")

# Mood options for manual logging
MOODS = [
    "Happy", "Calm", "Okay", "Worried", "Anxious", "Stressed",
    "Sad", "Angry", "Frustrated", "Tired"
]

# For charting: higher = better
MOOD_SCORE = {
    "Happy": 5,
    "Calm": 4,
    "Okay": 3,
    "Worried": 2,
    "Anxious": 2,
    "Stressed": 1,
    "Sad": 1,
    "Angry": 1,
    "Frustrated": 1,
    "Tired": 2,
}

# ---------- EMOTION MAPPING FOR AI DETECTION ----------
EMOTION_DATA = {
    # Positive emotions
    "Happy": {"emoji": "😊", "color": "success", "category": "Positive"},
    "Excited": {"emoji": "🎉", "color": "success", "category": "Positive"},
    "Calm": {"emoji": "😌", "color": "success", "category": "Positive"},
    "Grateful": {"emoji": "🙏", "color": "success", "category": "Positive"},
    "Hopeful": {"emoji": "✨", "color": "success", "category": "Positive"},
    
    # Anxious/Stressed
    "Anxious": {"emoji": "😰", "color": "warning", "category": "Anxious"},
    "Stressed": {"emoji": "😫", "color": "warning", "category": "Anxious"},
    "Overwhelmed": {"emoji": "😩", "color": "warning", "category": "Anxious"},
    "Scared": {"emoji": "😨", "color": "warning", "category": "Anxious"},
    
    # Sad/Lonely
    "Sad": {"emoji": "😢", "color": "error", "category": "Sad"},
    "Lonely": {"emoji": "💔", "color": "error", "category": "Sad"},
    "Empty": {"emoji": "🕳️", "color": "error", "category": "Sad"},
    "Tired": {"emoji": "😴", "color": "info", "category": "Tired"},
    
    # Angry/Frustrated
    "Angry": {"emoji": "😠", "color": "error", "category": "Angry"},
    "Frustrated": {"emoji": "😤", "color": "error", "category": "Angry"},
    
    # Guilty/Ashamed
    "Guilty": {"emoji": "😞", "color": "error", "category": "Guilty"},
    "Ashamed": {"emoji": "😶", "color": "error", "category": "Guilty"},
}

# ---------- CRISIS KEYWORDS (SINGAPORE CONTEXT) ----------
CRISIS_KEYWORDS = [
    # Self-harm methods
    "kill myself", "suicide", "want to die", "end my life", 
    "hurt myself", "stab myself", "cut myself", "slash",
    "hang myself", "jump off", "overdose", "shoot myself",
    "self-harm", "harm myself", "take my life", "end it all",
    "die", "dead", "kill", "slit", "wrist", "bleed",
    
    # Harm to others
    "kill someone", "hurt someone", "stab someone", "shoot someone",
    "hurt them", "kill them", "attack", "violent",
    
    # Distress indicators
    "hopeless", "worthless", "no reason to live",
    "can't go on", "give up", "better off dead"
]

# ---------- HELPER FUNCTIONS (DATA MANAGEMENT) ----------
def load_log() -> pd.DataFrame:
    """Load mood journal from CSV"""
    if os.path.exists(DATA_FILE):
        try:
            df = pd.read_csv(DATA_FILE)
            for col in ["date", "mood", "note", "score", "source"]:
                if col not in df.columns:
                    df[col] = "" if col != "score" else 3
            return df
        except Exception:
            return pd.DataFrame(columns=["date", "mood", "note", "score", "source"])
    return pd.DataFrame(columns=["date", "mood", "note", "score", "source"])

def save_entry(entry_date: str, mood: str, note: str, source: str = "manual"):
    """Save mood entry to CSV"""
    df = load_log()
    new_row = {
        "date": entry_date,
        "mood": mood,
        "note": note,
        "score": MOOD_SCORE.get(mood, 3),
        "source": source
    }
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    df.to_csv(DATA_FILE, index=False)

def analyze_with_gemini(journal_text: str):
    """Send text to Gemini AI for emotion analysis"""
    prompt_text = f"""
    You are a highly empathetic mental health assistant and mood analyzer.
    
    Read this journal entry and identify the **specific, real emotion** the person is feeling.
    
    Journal Entry: \"\"\"{journal_text}\"\"\"
    
    **YOUR TASK:**
    1. Identify the single most dominant emotion from this list: 
       Happy, Excited, Calm, Grateful, Hopeful, Anxious, Stressed, Overwhelmed, 
       Sad, Lonely, Angry, Frustrated, Tired, Empty, Scared, Ashamed, Guilty
    
    2. Write ONE short, warm sentence explaining why you think they feel this way.
    
    **FORMAT (exactly like this):**
    Emotion: [one word from list above]
    [Your empathetic explanation]
    
    Example:
    Emotion: Anxious
    You seem worried about things that haven't happened yet.
    
    Be specific. Don't just say "Positive" or "Negative" - find the real emotion.
    """
    
    try:
        response = GEMINI_MODEL.generate_content(prompt_text)
        result = response.text.strip()
        
        # Extract emotion
        lines = result.split('\n')
        emotion = "Neutral"
        explanation = result
        
        for line in lines:
            if line.lower().startswith("emotion:"):
                emotion = line.replace("Emotion:", "").replace("emotion:", "").strip()
                break
                
        return emotion, explanation
    except Exception as e:
        return "Error", f"AI analysis failed: {str(e)}"

def check_crisis_keywords(text: str) -> bool:
    """Check if text contains crisis keywords"""
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in CRISIS_KEYWORDS)

# ---------- UI COMPONENTS (CRISIS SUPPORT) ----------
def display_crisis_support():
    """Display Singapore-specific crisis support resources"""
    st.error("""
        🚨 **CRITICAL ALERT - IMMEDIATE HELP NEEDED** 🚨
        
        Your journal entry contains thoughts about harming yourself or others.
        
        **IN SINGAPORE, HELP IS AVAILABLE 24/7:**
        
        📞 **Samaritans of Singapore (SOS):** 1767
        💬 **SOS Care Text:** 9151 1767 (WhatsApp)
        🌐 **Chat Online:** https://www.sos.org.sg/
        
        🏥 **IMH Mental Health Helpline:** 6389 2222
        👥 **TOUCHline (Counselling):** 6804 6555
        🧑‍⚕️ **CHAT (Youth):** 6493 6500 / www.chat.mentalhealth.sg
        
        ---
        **Please reach out now. You are not alone. 💛**
        """)

def display_safety_block():
    """Display general safety resources (legacy function)"""
    st.markdown("### 🚨 Need Immediate Help? (Singapore)")
    st.markdown("""
- **Samaritans of Singapore (SOS)**: **1767** (24/7)
- **Institute of Mental Health (IMH) Mental Health Helpline**: **6389 2222** (24/7)
- **Singapore Association for Mental Health (SAMH)**: **1800 283 7019**
- **Singapore Children’s Society – Tinkle Friend**: **1800 274 4788** (for children & youth)

If you feel unsafe right now, please call one of the numbers above or reach out to a trusted adult immediately.
""")

def display_emotion_result(emotion: str, explanation: str):
    """Display emotion with proper emoji and color"""
    if emotion in EMOTION_DATA:
        emoji = EMOTION_DATA[emotion]["emoji"]
        color = EMOTION_DATA[emotion]["color"]
    else:
        emoji = "🧠"
        color = "info"
    
    if color == "success":
        st.success(f"{emoji} **{emotion}**\n\n{explanation}")
    elif color == "warning":
        st.warning(f"{emoji} **{emotion}**\n\n{explanation}")
    elif color == "error":
        st.error(f"{emoji} **{emotion}**\n\n{explanation}")
    else:
        st.info(f"{emoji} **{emotion}**\n\n{explanation}")

# ---------- SIDEBAR NAVIGATION ----------
st.sidebar.title("🧘 MindEase")
st.sidebar.caption("Your mental wellness companion")

page = st.sidebar.radio(
    "Navigate",
    ["📝 Journal", "🤖 AI Mood Analyzer", "📊 Mood History", "🧰 Self-Care Tools", "🆘 Support & Hotlines"],
    index=0
)

# Privacy disclaimer in sidebar
with st.sidebar.expander("📋 Privacy & Disclaimer", expanded=False):
    st.markdown("""
    **Privacy & Confidentiality**
    - No login required
    - Do not enter personal identifiers
    - Data stored locally in mood_log.csv
    
    **Disclaimer**
    This app provides self-care suggestions and is **not** a substitute for professional medical advice.
    """)

# ---------- MAIN CONTENT ----------
st.title("🌱 MindEase")
st.caption("A gentle space for journaling, emotional awareness, and self-care.")

# ---------- PAGE 1: JOURNAL ----------
if page == "📝 Journal":
    st.header("📝 Manual Mood Journal")
    st.write("Log how you're feeling today using the mood scale.")
    
    col1, col2 = st.columns(2)
    with col1:
        entry_date = st.date_input("Date", value=date.today()).isoformat()
    with col2:
        mood = st.selectbox("Select your mood", MOODS, index=MOODS.index("Okay"))
    
    note = st.text_area(
        "Journal notes (optional)",
        placeholder="What happened today? How are you feeling?",
        height=100
    )
    
    if st.button("💾 Save Entry", use_container_width=True):
        save_entry(entry_date, mood, note, source="manual")
        st.success("✅ Saved! View your entry in Mood History.")
    
    st.divider()
    st.markdown("""
    💡 **Tip:** Journaling works best when it's quick and consistent. 
    Even one sentence is enough to build the habit.
    """)

# ---------- PAGE 2: AI MOOD ANALYZER (YOUR INTEGRATED CODE) ----------
elif page == "🤖 AI Mood Analyzer":
    st.header("🤖 AI Mood Analyzer")
    st.write("Write freely, and let AI help you understand your emotions.")
    
    # AI Journal Input
    journal_entry = st.text_area(
        "How are you feeling right now?",
        placeholder="e.g., Today was really stressful. I have so much work and I feel like I can't catch up...",
        height=150
    )
    
    col1, col2 = st.columns([1, 3])
    with col1:
        analyze_button = st.button("🔍 Analyze Mood", type="primary", use_container_width=True)
    
    # Character counter
    if journal_entry:
        words = len(journal_entry.split())
        chars = len(journal_entry)
        st.caption(f"📊 {words} words • {chars} characters")
    
    # AI Analysis Section
    if analyze_button:
        if not journal_entry.strip():
            st.warning("Please write something to analyze.")
        else:
            # Step 1: Check for crisis keywords
            if check_crisis_keywords(journal_entry):
                display_crisis_support()
            else:
                # Step 2: Show analyzing state
                with st.spinner("🧠 AI is analyzing your emotions..."):
                    emotion, explanation = analyze_with_gemini(journal_entry)
                
                # Step 3: Display emotion result
                st.divider()
                st.subheader("🧠 AI Analysis Result")
                
                if emotion != "Error":
                    display_emotion_result(emotion, explanation)
                    
                    # Step 4: Save to history
                    save_entry(
                        entry_date=date.today().isoformat(),
                        mood=emotion,
                        note=journal_entry,
                        source="AI"
                    )
                    
                    # Step 5: Quick self-care suggestion based on emotion
                    st.divider()
                    st.subheader("💚 Quick Self-Care Suggestion")
                    
                    if emotion in ["Sad", "Lonely", "Empty"]:
                        st.info("**Try this:** Reach out to someone you trust. Connection helps.")
                        st.markdown("> *\"You are not alone in this.\"*")
                    elif emotion in ["Anxious", "Stressed", "Overwhelmed", "Scared"]:
                        st.info("**Try this:** Box breathing - Inhale 4, Hold 4, Exhale 4, Hold 4. Repeat 3 times.")
                        st.markdown("> *\"This feeling will pass.\"*")
                    elif emotion in ["Angry", "Frustrated"]:
                        st.info("**Try this:** Step away for 5 minutes. Drink water. Move your body.")
                        st.markdown("> *\"It's okay to feel angry. What you do with it matters.\"*")
                    elif emotion in ["Tired"]:
                        st.info("**Try this:** Rest is productive too. Give yourself permission to pause.")
                        st.markdown("> *\"You've been doing your best.\"*")
                    elif emotion in ["Happy", "Excited", "Calm", "Grateful", "Hopeful"]:
                        st.success("**Try this:** Savor this moment. What's one thing that went well today?")
                        st.markdown("> *\"Small joys add up.\"*")
                else:
                    st.error(explanation)
    
    # Recent AI entries preview
    st.divider()
    st.subheader("📋 Recent AI Analysis")
    df = load_log()
    ai_entries = df[df["source"] == "AI"].sort_values(by="date", ascending=False).head(3)
    
    if not ai_entries.empty:
        for _, row in ai_entries.iterrows():
            with st.container():
                mood = row["mood"]
                emoji = EMOTION_DATA.get(mood, {}).get("emoji", "📝")
                st.markdown(f"**{emoji} {mood}** - {row['date']}")
                st.caption(row["note"][:100] + "..." if len(row["note"]) > 100 else row["note"])
                st.markdown("---")
    else:
        st.info("No AI analyses yet. Try the analyzer above!")

# ---------- PAGE 3: MOOD HISTORY ----------
elif page == "📊 Mood History":
    st.header("📊 Mood History & Trends")
    
    df = load_log()
    if df.empty:
        st.info("No entries yet. Go to Journal or AI Mood Analyzer to add your first entry.")
    else:
        # Clean data
        df["score"] = pd.to_numeric(df.get("score", 3), errors="coerce").fillna(3)
        df["date"] = df["date"].astype(str)
        
        # Parse dates
        try:
            df["_date"] = pd.to_datetime(df["date"])
        except Exception:
            df["_date"] = pd.NaT
        
        # Filter by source
        source_filter = st.radio(
            "Show entries from:",
            ["All", "Manual", "AI"],
            horizontal=True
        )
        
        filtered_df = df.copy()
        if source_filter == "Manual":
            filtered_df = df[df["source"] == "manual"]
        elif source_filter == "AI":
            filtered_df = df[df["source"] == "AI"]
        
        # Display entries
        st.subheader("Your Journal Entries")
        show_notes = st.checkbox("Show full notes", value=False)
        
        view_cols = ["date", "mood", "source"]
        if show_notes:
            view_cols.append("note")
        
        st.dataframe(
            filtered_df[view_cols].sort_values(by="date", ascending=False),
            use_container_width=True,
            hide_index=True
        )
        
        # Mood trend chart
        st.subheader("Mood Trend Over Time")
        chart_df = filtered_df.dropna(subset=["_date"]).sort_values(by="_date")
        
        if chart_df.empty:
            st.warning("Could not generate chart for the selected filter.")
        else:
            # Convert mood names to scores for charting
            chart_df["chart_score"] = chart_df["mood"].map(
                lambda x: EMOTION_DATA.get(x, {}).get("score", 3) if x in EMOTION_DATA 
                else MOOD_SCORE.get(x, 3)
            )
            st.line_chart(chart_df.set_index("_date")["chart_score"])
        
        # Emotion distribution
        st.subheader("Emotion Distribution")
        mood_counts = filtered_df["mood"].value_counts().reset_index()
        mood_counts.columns = ["Emotion", "Count"]
        
        # Add emojis to emotion names
        mood_counts["Emotion with Emoji"] = mood_counts["Emotion"].apply(
            lambda x: f"{EMOTION_DATA.get(x, {}).get('emoji', '📌')} {x}" if x in EMOTION_DATA else x
        )
        
        st.bar_chart(mood_counts.set_index("Emotion with Emoji")["Count"])
        
        # Clear data button
        st.divider()
        with st.expander("⚠️ Data Management"):
            st.warning("This will permanently delete all saved journal entries.")
            if st.button("Clear All Entries", type="secondary"):
                if os.path.exists(DATA_FILE):
                    os.remove(DATA_FILE)
                st.success("All entries cleared. Refresh the page.")
                st.rerun()

# ---------- PAGE 4: SELF-CARE TOOLS ----------
elif page == "🧰 Self-Care Tools":
    st.header("🧰 Self-Care Toolbox")
    st.write("Quick exercises to help you ground and center yourself.")
    
    tool = st.selectbox(
        "Choose a tool",
        ["Breathing Exercise", "5-4-3-2-1 Grounding", "Affirmations", "Journal Prompts"]
    )
    
    if tool == "Breathing Exercise":
        st.subheader("🌬️ Box Breathing")
        st.write("**Pattern:** Inhale 4 → Hold 4 → Exhale 4 → Hold 4")
        
        cycles = st.slider("Number of cycles", 2, 8, 4)
        total_seconds = cycles * 16
        
        st.info(f"⏱️ Total time: ~{total_seconds} seconds")
        
        if st.button("Start Breathing Timer", use_container_width=True):
            with st.spinner(f"Breathing exercise in progress..."):
                import time
                progress_bar = st.progress(0)
                for i in range(cycles * 4):  # 4 steps per cycle
                    time.sleep(1)
                    progress_bar.progress((i + 1) / (cycles * 4))
            st.success("✨ Complete! How do you feel?")
    
    elif tool == "5-4-3-2-1 Grounding":
        st.subheader("👁️ 5-4-3-2-1 Grounding")
        st.write("Name...")
        
        col1, col2 = st.columns(2)
        with col1:
            st.text_input("5 things you can SEE", placeholder="e.g., lamp, window, cup...")
            st.text_input("4 things you can FEEL", placeholder="e.g., chair, fabric, breeze...")
            st.text_input("3 things you can HEAR", placeholder="e.g., fan, birds, typing...")
        with col2:
            st.text_input("2 things you can SMELL", placeholder="e.g., coffee, fresh air...")
            st.text_input("1 thing you can TASTE", placeholder="e.g., mint, water...")
        
        st.caption("This exercise helps bring you back to the present moment.")
    
    elif tool == "Affirmations":
        st.subheader("💬 Daily Affirmations")
        
        affirmations = [
            "I am doing the best I can, and that is enough.",
            "My feelings are valid, and they will pass.",
            "I deserve kindness, especially from myself.",
            "It's okay to ask for help when I need it.",
            "I don't have to be perfect to be worthy.",
            "This moment is temporary. I can get through it.",
            "I am allowed to rest. I am allowed to heal."
        ]
        
        if st.button("✨ Give me an affirmation", use_container_width=True):
            import random
            affirmation = random.choice(affirmations)
            st.success(f"💛 {affirmation}")
    
    else:  # Journal Prompts
        st.subheader("📝 Gentle Journal Prompts")
        
        prompts = [
            "What's one thing I can control today?",
            "What small moment brought me peace recently?",
            "If my best friend felt this way, what would I tell them?",
            "What's one thing I did well today, even if small?",
            "What do I need right now, in this moment?",
            "What's something I'm looking forward to?",
            "What's one kind thing I can do for myself today?"
        ]
        
        for prompt in prompts:
            st.markdown(f"- {prompt}")

# ---------- PAGE 5: SUPPORT & HOTLINES ----------
else:  # Support & Hotlines
    st.header("🆘 Crisis Support - Singapore")
    
    display_safety_block()
    
    st.divider()
    
    st.subheader("📱 Additional Resources")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **🧑‍🤝‍🧑 For Youth**
        - **CHAT (youth mental health)**: 6493 6500
        - **Tinkle Friend**: 1800 274 4788
        - **eCounselling Centre**: chat.mentalhealth.sg
        
        **👨‍👩‍👧 For Families**
        - **Care Corner Counselling**: 1800 353 5800
        - **Fei Yue Family Service**: 6819 9170
        """)
    
    with col2:
        st.markdown("""
        **🏥 Professional Help**
        - **IMH Appointment**: 6389 2000
        - **SGH Psychiatry**: 6321 4377
        - **NUH Psychiatry**: 6772 2000
        
        **💻 Online Support**
        - **SOS Chat**: www.sos.org.sg
        - **Mindline.sg**: www.mindline.sg
        """)
    
    st.divider()
    st.warning("""
    **If you or someone else is in immediate danger, please call 995 now.**
    
    These helplines are confidential and staffed by trained professionals.
    You don't need to be in crisis to call - they're here to listen.
    """)
