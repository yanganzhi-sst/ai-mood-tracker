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
    "Happy": {"emoji": "😊", "color": "success", "category": "Positive", "score": 5},
    "Excited": {"emoji": "🎉", "color": "success", "category": "Positive", "score": 5},
    "Calm": {"emoji": "😌", "color": "success", "category": "Positive", "score": 4},
    "Grateful": {"emoji": "🙏", "color": "success", "category": "Positive", "score": 4},
    "Hopeful": {"emoji": "✨", "color": "success", "category": "Positive", "score": 4},
    
    # Anxious/Stressed
    "Anxious": {"emoji": "😰", "color": "warning", "category": "Anxious", "score": 2},
    "Stressed": {"emoji": "😫", "color": "warning", "category": "Anxious", "score": 2},
    "Overwhelmed": {"emoji": "😩", "color": "warning", "category": "Anxious", "score": 1},
    "Scared": {"emoji": "😨", "color": "warning", "category": "Anxious", "score": 1},
    
    # Sad/Lonely
    "Sad": {"emoji": "😢", "color": "error", "category": "Sad", "score": 1},
    "Lonely": {"emoji": "💔", "color": "error", "category": "Sad", "score": 1},
    "Empty": {"emoji": "🕳️", "color": "error", "category": "Sad", "score": 1},
    "Tired": {"emoji": "😴", "color": "info", "category": "Tired", "score": 2},
    
    # Angry/Frustrated
    "Angry": {"emoji": "😠", "color": "error", "category": "Angry", "score": 1},
    "Frustrated": {"emoji": "😤", "color": "error", "category": "Angry", "score": 1},
    
    # Guilty/Ashamed
    "Guilty": {"emoji": "😞", "color": "error", "category": "Guilty", "score": 1},
    "Ashamed": {"emoji": "😶", "color": "error", "category": "Guilty", "score": 1},
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

def save_entry(mood: str, note: str, source: str = "manual"):
    """Save mood entry to CSV with today's date"""
    entry_date = date.today().isoformat()
    df = load_log()
    
    # Get score based on source
    if source == "AI" and mood in EMOTION_DATA:
        score = EMOTION_DATA[mood]["score"]
    else:
        score = MOOD_SCORE.get(mood, 3)
    
    new_row = {
        "date": entry_date,
        "mood": mood,
        "note": note,
        "score": score,
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
    """Display general safety resources"""
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

# ---------- SIDEBAR - MODERN NAVIGATION BUTTONS ----------
st.sidebar.markdown("""
<style>
    /* Hide default radio indicators */
    div.row-widget.stRadio > div {
        flex-direction: column;
        gap: 8px;
    }
    div.row-widget.stRadio > div[role="radiogroup"] > label {
        background: white;
        border: 1px solid #e0e0e0;
        border-radius: 12px;
        padding: 12px 16px;
        margin: 0;
        transition: all 0.2s;
        display: flex;
        align-items: center;
        gap: 12px;
        font-weight: 500;
    }
    div.row-widget.stRadio > div[role="radiogroup"] > label:hover {
        background: #f8f9fa;
        border-color: #9aa0a6;
        transform: translateY(-1px);
    }
    div.row-widget.stRadio > div[role="radiogroup"] > label[data-baseweb="radio"] > div:first-child {
        display: none !important;
    }
    div.row-widget.stRadio > div[role="radiogroup"] > label[aria-checked="true"] {
        background: #e8f0fe;
        border-color: #1a73e8;
        color: #1a73e8;
        font-weight: 600;
    }
    /* Hide the actual radio circle */
    div.row-widget.stRadio > div[role="radiogroup"] > label > div:first-child {
        display: none;
    }
</style>
""", unsafe_allow_html=True)

st.sidebar.markdown("# 🌱 MindEase")
st.sidebar.markdown("---")

# Navigation buttons (styled as cards)
nav_options = {
    "📝 Journal": "Write & track moods",
    "🤖 AI Analyzer": "AI-powered insights", 
    "📊 History": "View your journey",
    "🧰 Self-Care": "Tools & exercises",
    "🆘 Crisis Help": "24/7 Singapore support"
}

# Initialize session state for navigation if not exists
if "page" not in st.session_state:
    st.session_state.page = "📝 Journal"

# Create navigation buttons
for option, desc in nav_options.items():
    col1, col2 = st.sidebar.columns([1, 5])
    with col1:
        st.markdown(f"### {option.split()[0]}")
    with col2:
        if st.button(
            f"{option.split()[1] if len(option.split()) > 1 else ''}",
            key=f"nav_{option}",
            use_container_width=True,
            type="primary" if st.session_state.page == option else "secondary"
        ):
            st.session_state.page = option
            st.rerun()
    st.sidebar.caption(desc)
    st.sidebar.markdown("---")

# Today's date and greeting
today = date.today()
st.sidebar.markdown(f"""
### 📅 {today.strftime('%A, %d %B %Y')}
*{today.strftime('%B')} {today.strftime('%d')}, {today.strftime('%Y')}*
""")

# Quick stats
df = load_log()
if not df.empty:
    today_entries = df[df["date"] == today.isoformat()]
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📊 Today")
    st.sidebar.markdown(f"Entries: **{len(today_entries)}**")
    if not today_entries.empty:
        st.sidebar.markdown(f"Latest: **{today_entries.iloc[-1]['mood']}**")

# Privacy disclaimer in sidebar (collapsible)
with st.sidebar.expander("🔒 Privacy & Safety", expanded=False):
    st.markdown("""
    **Your data stays on your device**
    - No login required
    - No cloud storage
    - CSV file saved locally
    
    **Not a medical tool**
    - For self-reflection only
    - Not a substitute for professional help
    """)

# ---------- MAIN CONTENT ----------
# Get current page from session state
page = st.session_state.page

# ---------- PAGE 1: JOURNAL ----------
if page == "📝 Journal":
    st.title("📝 Journal Your Day")
    st.caption(f"Today • {date.today().strftime('%A, %d %B %Y')}")
    
    col1, col2 = st.columns([1, 1])
    with col1:
        st.markdown("### How are you feeling?")
        mood = st.selectbox("Select your mood", MOODS, index=MOODS.index("Okay"), label_visibility="collapsed")
    
    note = st.text_area(
        "What's on your mind?",
        placeholder="Write freely... what happened today? How are you feeling?",
        height=150
    )
    
    if st.button("💾 Save Entry", use_container_width=True, type="primary"):
        if not note.strip():
            st.warning("Add a few words about your day before saving.")
        else:
            save_entry(mood, note, source="manual")
            st.success("✅ Saved! Your entry has been added to your history.")
    
    st.divider()
    st.markdown("""
    💡 **Journaling tip:** Try to write without judgment. There's no right or wrong way to journal.
    """)

# ---------- PAGE 2: AI MOOD ANALYZER ----------
elif page == "🤖 AI Analyzer":
    st.title("🤖 AI Mood Analyzer")
    st.caption(f"Today • {date.today().strftime('%A, %d %B %Y')}")
    st.write("Write freely - the AI will help you understand your emotions.")
    
    journal_entry = st.text_area(
        "How are you feeling right now?",
        placeholder="e.g., I'm feeling overwhelmed with work and I don't know where to start...",
        height=150
    )
    
    # Character counter
    if journal_entry:
        words = len(journal_entry.split())
        chars = len(journal_entry)
        st.caption(f"📝 {words} words • {chars} characters")
    
    col1, col2 = st.columns([1, 3])
    with col1:
        analyze_button = st.button("🔍 Analyze", type="primary", use_container_width=True)
    
    if analyze_button:
        if not journal_entry.strip():
            st.warning("Please write something to analyze.")
        else:
            # Check for crisis keywords
            if check_crisis_keywords(journal_entry):
                display_crisis_support()
            else:
                with st.spinner("🧠 AI is analyzing your emotions..."):
                    emotion, explanation = analyze_with_gemini(journal_entry)
                
                st.divider()
                st.subheader("🧠 Analysis Result")
                
                if emotion != "Error":
                    display_emotion_result(emotion, explanation)
                    
                    # Save to history
                    save_entry(emotion, journal_entry, source="AI")
                    
                    # Quick self-care suggestion
                    st.divider()
                    st.subheader("💚 Quick Self-Care")
                    
                    if emotion in ["Sad", "Lonely", "Empty"]:
                        st.info("**Try this:** Reach out to someone you trust. You don't have to go through this alone.")
                        st.markdown("> *\"You are not alone in this.\"*")
                    elif emotion in ["Anxious", "Stressed", "Overwhelmed", "Scared"]:
                        st.info("**Try this:** Take 3 deep breaths. Breathe in for 4, out for 4.")
                        st.markdown("> *\"This feeling will pass. You've gotten through hard days before.\"*")
                    elif emotion in ["Angry", "Frustrated"]:
                        st.info("**Try this:** Step away for 5 minutes. Drink water. Your feelings are valid.")
                        st.markdown("> *\"It's okay to feel angry. What matters is how you respond.\"*")
                    elif emotion in ["Tired"]:
                        st.info("**Try this:** Rest is productive too. Give yourself permission to pause.")
                        st.markdown("> *\"You've been doing your best. That's enough.\"*")
                    elif emotion in ["Happy", "Excited", "Calm", "Grateful", "Hopeful"]:
                        st.success("**Try this:** Savor this moment. What's one thing you're grateful for right now?")
                        st.markdown("> *\"Small joys add up.\"*")
                else:
                    st.error(explanation)
    
    # Show recent AI entries
    st.divider()
    st.subheader("📋 Recent AI Analyses")
    df = load_log()
    ai_entries = df[df["source"] == "AI"].sort_values(by="date", ascending=False).head(3)
    
    if not ai_entries.empty:
        for _, row in ai_entries.iterrows():
            with st.container():
                mood = row["mood"]
                emoji = EMOTION_DATA.get(mood, {}).get("emoji", "📝")
                st.markdown(f"**{emoji} {mood}** — {row['date']}")
                st.caption(row["note"][:100] + "..." if len(row["note"]) > 100 else row["note"])
                st.divider()
    else:
        st.info("No AI analyses yet. Try the analyzer above!")

# ---------- PAGE 3: HISTORY ----------
elif page == "📊 History":
    st.title("📊 Your Mood History")
    
    df = load_log()
    if df.empty:
        st.info("No entries yet. Start by journaling or using the AI analyzer.")
    else:
        # Filter by date range
        col1, col2 = st.columns(2)
        with col1:
            filter_option = st.selectbox(
                "Show",
                ["All time", "Last 7 days", "Last 30 days", "This month"],
                index=0
            )
        
        # Apply date filter
        df["date"] = pd.to_datetime(df["date"])
        
        if filter_option == "Last 7 days":
            cutoff = pd.Timestamp.now() - pd.Timedelta(days=7)
            df = df[df["date"] >= cutoff]
        elif filter_option == "Last 30 days":
            cutoff = pd.Timestamp.now() - pd.Timedelta(days=30)
            df = df[df["date"] >= cutoff]
        elif filter_option == "This month":
            df = df[df["date"].dt.month == pd.Timestamp.now().month]
        
        with col2:
            source_filter = st.selectbox(
                "Type",
                ["All entries", "Manual only", "AI only"],
                index=0
            )
        
        if source_filter == "Manual only":
            df = df[df["source"] == "manual"]
        elif source_filter == "AI only":
            df = df[df["source"] == "AI"]
        
        # Sort by date
        df = df.sort_values("date", ascending=False)
        
        # Metrics
        st.subheader("Overview")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total entries", len(df))
        with col2:
            if not df.empty:
                avg_score = df["score"].mean()
                st.metric("Average mood", f"{avg_score:.1f}/5")
        with col3:
            if not df.empty:
                most_common = df["mood"].mode()[0] if not df["mood"].mode().empty else "N/A"
                emoji = EMOTION_DATA.get(most_common, {}).get("emoji", "")
                st.metric("Most frequent", f"{emoji} {most_common}")
        with col4:
            if not df.empty:
                today_count = len(df[df["date"].dt.date == date.today()])
                st.metric("Today", today_count)
        
        # Mood trend chart
        st.subheader("Mood Trend")
        chart_df = df.sort_values("date")
        if not chart_df.empty:
            st.line_chart(chart_df.set_index("date")["score"])
        
        # Emotion distribution
        st.subheader("Emotion Distribution")
        mood_counts = df["mood"].value_counts().head(8)
        
        # Add emojis to labels
        mood_labels = []
        for mood in mood_counts.index:
            emoji = EMOTION_DATA.get(mood, {}).get("emoji", "📌")
            mood_labels.append(f"{emoji} {mood}")
        
        # Create bar chart
        chart_data = pd.DataFrame({
            "Emotion": mood_labels,
            "Count": mood_counts.values
        })
        st.bar_chart(chart_data.set_index("Emotion"))
        
        # Detailed entries
        st.subheader("Recent Entries")
        for _, row in df.head(10).iterrows():
            with st.container():
                col1, col2 = st.columns([1, 5])
                with col1:
                    mood = row["mood"]
                    emoji = EMOTION_DATA.get(mood, {}).get("emoji", "📝")
                    source_icon = "📝" if row["source"] == "manual" else "🤖"
                    st.markdown(f"**{emoji}**")
                    st.caption(f"{source_icon} {row['source']}")
                with col2:
                    st.markdown(f"**{mood}** • {row['date'].strftime('%b %d, %Y')}")
                    if pd.notna(row["note"]) and row["note"]:
                        st.caption(row["note"][:150] + "..." if len(row["note"]) > 150 else row["note"])
                st.divider()
        
        # Clear data button
        with st.expander("⚠️ Data Management"):
            st.warning("This will permanently delete all your saved journal entries.")
            if st.button("Clear All Data", type="secondary"):
                if os.path.exists(DATA_FILE):
                    os.remove(DATA_FILE)
                st.success("All entries cleared.")
                st.rerun()

# ---------- PAGE 4: SELF-CARE ----------
elif page == "🧰 Self-Care":
    st.title("🧰 Self-Care Toolbox")
    st.caption("Quick exercises to help you feel grounded")
    
    tabs = st.tabs(["🌬️ Breathing", "👁️ Grounding", "💬 Affirmations", "📝 Prompts"])
    
    with tabs[0]:  # Breathing
        st.subheader("Box Breathing")
        st.write("**4-4-4-4 Technique:** Inhale → Hold → Exhale → Hold")
        
        cycles = st.slider("Number of cycles", 2, 8, 4)
        
        if st.button("Start Breathing Exercise", use_container_width=True):
            with st.spinner(f"Breathing exercise in progress..."):
                import time
                progress_bar = st.progress(0)
                total_steps = cycles * 4
                for i in range(total_steps):
                    time.sleep(1)
                    progress_bar.progress((i + 1) / total_steps)
            st.success("✨ Complete! Notice how you feel now.")
    
    with tabs[1]:  # Grounding
        st.subheader("5-4-3-2-1 Grounding")
        st.write("Name...")
        
        col1, col2 = st.columns(2)
        with col1:
            st.text_input("5 things you can **SEE**", placeholder="lamp, window, cup...")
            st.text_input("4 things you can **FEEL**", placeholder="chair, fabric, breeze...")
            st.text_input("3 things you can **HEAR**", placeholder="fan, birds, typing...")
        with col2:
            st.text_input("2 things you can **SMELL**", placeholder="coffee, fresh air...")
            st.text_input("1 thing you can **TASTE**", placeholder="mint, water...")
        
        st.caption("This exercise brings you back to the present moment.")
    
    with tabs[2]:  # Affirmations
        st.subheader("Daily Affirmations")
        
        affirmations = [
            "I am doing the best I can, and that is enough.",
            "My feelings are valid, and they will pass.",
            "I deserve kindness, especially from myself.",
            "It's okay to ask for help when I need it.",
            "I don't have to be perfect to be worthy.",
            "This moment is temporary. I can get through this.",
            "I am allowed to rest. I am allowed to heal."
        ]
        
        if st.button("✨ Show me an affirmation", use_container_width=True):
            import random
            affirmation = random.choice(affirmations)
            st.success(f"💛 {affirmation}")
    
    with tabs[3]:  # Prompts
        st.subheader("Gentle Journal Prompts")
        
        prompts = [
            "What's one thing I can control today?",
            "What small moment brought me peace recently?",
            "If my best friend felt this way, what would I tell them?",
            "What's one thing I did well today, even if small?",
            "What do I need right now, in this moment?",
            "What's something I'm looking forward to?"
        ]
        
        for prompt in prompts:
            st.markdown(f"- {prompt}")

# ---------- PAGE 5: CRISIS HELP ----------
else:  # Crisis Help
    st.title("🆘 Crisis Support - Singapore")
    st.caption("24/7 confidential helplines")
    
    display_safety_block()
    
    st.divider()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### 🧑‍🤝‍🧑 For Youth
        - **CHAT (youth mental health)**: 6493 6500
        - **Tinkle Friend**: 1800 274 4788
        - **eCounselling Centre**: chat.mentalhealth.sg
        
        ### 👨‍👩‍👧 For Families
        - **Care Corner Counselling**: 1800 353 5800
        - **Fei Yue Family Service**: 6819 9170
        """)
    
    with col2:
        st.markdown("""
        ### 🏥 Professional Help
        - **IMH Appointment**: 6389 2000
        - **SGH Psychiatry**: 6321 4377
        - **NUH Psychiatry**: 6772 2000
        
        ### 💻 Online Support
        - **SOS Chat**: sos.org.sg
        - **Mindline.sg**: mindline.sg
        - **EC2 (SAMH)**: samhealth.org.sg
        """)
    
    st.divider()
    st.warning("""
    **If you or someone else is in immediate danger, please call 995 now.**
    
    These helplines are confidential and staffed by trained professionals.
    You don't need to be in crisis to call - they're here to listen.
    """)
