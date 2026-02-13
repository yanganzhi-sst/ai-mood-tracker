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

# For charting: higher = better
MOOD_SCORE = {
    "Happy": 5, "Excited": 5, "Calm": 4, "Grateful": 4, "Hopeful": 4,
    "Anxious": 2, "Stressed": 2, "Overwhelmed": 1, "Scared": 1,
    "Sad": 1, "Lonely": 1, "Empty": 1, "Tired": 2,
    "Angry": 1, "Frustrated": 1, "Guilty": 1, "Ashamed": 1,
    "Okay": 3, "Worried": 2, "Neutral": 3
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
    
    # Neutral/Fallback
    "Okay": {"emoji": "😐", "color": "info", "category": "Neutral", "score": 3},
    "Neutral": {"emoji": "😐", "color": "info", "category": "Neutral", "score": 3},
    "Worried": {"emoji": "😟", "color": "warning", "category": "Anxious", "score": 2}
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

def save_entry(mood: str, note: str, source: str = "ai"):
    """Save mood entry to CSV with today's date"""
    entry_date = date.today().isoformat()
    df = load_log()
    
    # Get score based on emotion
    score = EMOTION_DATA.get(mood, {}).get("score", 3)
    
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
       Sad, Lonely, Angry, Frustrated, Tired, Empty, Scared, Ashamed, Guilty, Worried, Okay, Neutral
    
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
        return "Neutral", f"AI analysis unavailable. Your entry was saved."

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
- **Singapore Children's Society – Tinkle Friend**: **1800 274 4788** (for children & youth)

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

# ---------- SIDEBAR - BLACK MAC-FRIENDLY NAVIGATION ----------
st.sidebar.markdown("""
<style>
    /* Clean, black styling for Mac */
    [data-testid="stSidebar"] {
        background-color: #000000 !important;
        padding: 20px 0px;
    }
    
    /* App title - white on black */
    .sidebar-title {
        font-size: 28px;
        font-weight: 600;
        color: #ffffff;
        margin-bottom: 8px;
        letter-spacing: -0.5px;
        padding-left: 20px;
    }
    
    /* BIG DATE STYLING - black card */
    .big-date {
        background: #1a1a1a;
        padding: 20px 20px;
        border-radius: 16px;
        margin: 16px 20px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        border: 1px solid #333333;
    }
    .day-name {
        font-size: 18px;
        font-weight: 500;
        color: #b0b0b0;
        margin-bottom: 4px;
        letter-spacing: -0.2px;
    }
    .day-date {
        font-size: 32px;
        font-weight: 700;
        color: #ffffff;
        line-height: 1.2;
        letter-spacing: -1px;
    }
    .month-year {
        font-size: 18px;
        font-weight: 500;
        color: #b0b0b0;
        margin-top: 4px;
    }
    
    /* Clean nav buttons - black theme */
    .nav-item {
        padding: 10px 20px;
        margin: 2px 0px;
        border-radius: 0px;
        font-weight: 500;
        color: #e0e0e0;
        transition: all 0.1s;
        display: flex;
        align-items: center;
        gap: 12px;
        border-left: 3px solid transparent;
    }
    .nav-item:hover {
        background-color: #2a2a2a;
        border-left: 3px solid #808080;
        color: #ffffff;
    }
    .nav-item-active {
        background-color: #1a33a8 !important;
        border-left: 3px solid #4d94ff !important;
        color: #ffffff !important;
        font-weight: 600;
    }
    .nav-icon {
        font-size: 20px;
        width: 28px;
        text-align: center;
    }
    
    /* Stats card - black theme */
    .stats-card {
        background: #1a1a1a;
        padding: 16px 20px;
        border-radius: 12px;
        margin: 8px 20px;
        border: 1px solid #333333;
    }
    .stats-label {
        font-size: 14px;
        color: #b0b0b0;
        margin-bottom: 4px;
    }
    .stats-number {
        font-size: 28px;
        font-weight: 700;
        color: #ffffff;
    }
    
    /* Divider - dark grey */
    .sidebar-divider {
        margin: 16px 20px;
        border-top: 1px solid #333333;
    }
    
    /* Expander in sidebar - black theme */
    .streamlit-expanderHeader {
        color: #e0e0e0 !important;
        background-color: #1a1a1a !important;
    }
    .streamlit-expanderContent {
        background-color: #1a1a1a !important;
        color: #e0e0e0 !important;
    }
    
    /* Make primary button greener */
    .stButton button[kind="primary"] {
        background-color: #0B6623 !important;
        color: white !important;
        font-weight: 600 !important;
    }
    .stButton button[kind="primary"]:hover {
        background-color: #0A5C1F !important;
        color: white !important;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# App title
st.sidebar.markdown('<div class="sidebar-title">🌱 MindEase</div>', unsafe_allow_html=True)

# ---------- BIG DATE DISPLAY ----------
today = date.today()
st.sidebar.markdown(f'''
<div class="big-date">
    <div class="day-name">{today.strftime("%A")}</div>
    <div class="day-date">{today.strftime("%d")}</div>
    <div class="month-year">{today.strftime("%B %Y")}</div>
</div>
''', unsafe_allow_html=True)

# Navigation options - ONLY 4 PAGES
nav_items = [
    {"icon": "📝", "label": "Journal", "id": "journal"},
    {"icon": "📊", "label": "History", "id": "history"},
    {"icon": "🧰", "label": "Self-Care", "id": "selfcare"},
    {"icon": "🆘", "label": "Crisis Help", "id": "crisis"}
]

# Initialize session state for navigation
if "current_page" not in st.session_state:
    st.session_state.current_page = "journal"

# Create navigation buttons
for item in nav_items:
    active_class = "nav-item-active" if st.session_state.current_page == item["id"] else ""
    
    # Create columns for icon and label
    cols = st.sidebar.columns([1, 5])
    
    with cols[0]:
        st.markdown(f'<div class="nav-icon">{item["icon"]}</div>', unsafe_allow_html=True)
    
    with cols[1]:
        if st.button(
            item["label"],
            key=f"nav_{item['id']}",
            use_container_width=True
        ):
            st.session_state.current_page = item["id"]
            st.rerun()

# Quick stats
st.sidebar.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)

df = load_log()
if not df.empty:
    today_entries = df[df["date"] == today.isoformat()]
    
    st.sidebar.markdown('<div class="stats-card">', unsafe_allow_html=True)
    st.sidebar.markdown('<div class="stats-label">Today\'s entries</div>', unsafe_allow_html=True)
    st.sidebar.markdown(f'<div class="stats-number">{len(today_entries)}</div>', unsafe_allow_html=True)
    
    if not today_entries.empty:
        latest_mood = today_entries.iloc[-1]["mood"]
        emoji = EMOTION_DATA.get(latest_mood, {}).get("emoji", "📝")
        st.sidebar.markdown(f'<div style="margin-top: 12px; font-size: 16px; color: white;">Latest: {emoji} {latest_mood}</div>', unsafe_allow_html=True)
    st.sidebar.markdown('</div>', unsafe_allow_html=True)
else:
    st.sidebar.markdown('<div class="stats-card">', unsafe_allow_html=True)
    st.sidebar.markdown('<div class="stats-label">Welcome!</div>', unsafe_allow_html=True)
    st.sidebar.markdown('<div style="font-size: 16px; margin-top: 8px; color: white;">Start your first entry ✨</div>', unsafe_allow_html=True)
    st.sidebar.markdown('</div>', unsafe_allow_html=True)

# Privacy footer
st.sidebar.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)
with st.sidebar.expander("🔒 Private & Local", expanded=False):
    st.markdown("""
    • No login needed  
    • Data stays on your device  
    • Not medical advice  
    • 24/7 crisis support available
    """)

# ---------- SET CURRENT PAGE BASED ON NAVIGATION ----------
page_map = {
    "journal": "📝 Journal",
    "history": "📊 History",
    "selfcare": "🧰 Self-Care",
    "crisis": "🆘 Crisis Help"
}
page = page_map[st.session_state.current_page]

# ---------- MAIN CONTENT ----------
# ---------- PAGE 1: JOURNAL - UNIFIED, AUTO-ANALYZE ----------
if page == "📝 Journal":
    st.title("📝 MindEase Journal")
    st.caption(f"Today • {today.strftime('%A, %d %B %Y')}")
    
    # Single journal text area - this is the ONLY input
    journal_entry = st.text_area(
        "How are you feeling?",
        placeholder="Write anything... I'll understand how you're feeling and suggest ways to help.",
        height=200
    )
    
    # Character counter
    if journal_entry:
        words = len(journal_entry.split())
        chars = len(journal_entry)
        st.caption(f"📝 {words} words • {chars} characters")
    
    # Green save & analyze button
    save_button = st.button("💾 Save & Analyze Entry", use_container_width=True, type="primary", key="save_analyze")
    
    if save_button:
        if not journal_entry.strip():
            st.warning("Please write something before saving.")
        else:
            # Check for crisis keywords FIRST
            if check_crisis_keywords(journal_entry):
                display_crisis_support()
                # Save as crisis entry
                save_entry("Crisis", journal_entry, source="crisis")
                st.success("✅ Entry saved. Please reach out for support.")
            else:
                # Analyze with Gemini
                with st.spinner("🧠 Analyzing your emotions..."):
                    emotion, explanation = analyze_with_gemini(journal_entry)
                
                # Display result in a beautiful container
                st.divider()
                
                # Show emotion result
                display_emotion_result(emotion, explanation)
                
                # Save to history
                save_entry(emotion, journal_entry, source="ai")
                st.success("✅ Journal saved and analyzed!")
                
                # ---------- BETTER SELF-CARE SUGGESTIONS ----------
                st.divider()
                st.subheader("💚 Personalized Self-Care")
                
                # Create expandable sections for each emotion type
                if emotion in ["Happy", "Excited", "Calm", "Grateful", "Hopeful"]:
                    with st.expander("🌿 Savor This Moment", expanded=True):
                        st.markdown("""
                        **You're in a positive space right now. Here's how to nurture it:**
                        
                        ✨ **Gratitude pause** - What's one thing you're thankful for right now?
                        📝 **Capture this feeling** - Write down what's going well
                        🌅 **Savor** - Take 30 seconds to really feel this moment
                        🎵 **Celebrate** - Listen to a song that matches your mood
                        
                        > *"Happiness is not something you postpone for the future; it is something you design for the present."*
                        """)
                
                elif emotion in ["Anxious", "Stressed", "Overwhelmed", "Scared", "Worried"]:
                    with st.expander("🌀 Calm Your Mind", expanded=True):
                        st.markdown("""
                        **Your nervous system needs soothing right now. Try these:**
                        
                        🌬️ **4-7-8 Breathing** - Inhale 4, Hold 7, Exhale 8 (repeat 4x)
                        🖐️ **Palm pressure** - Press your thumb into your opposite palm
                        ❄️ **Cold splash** - Run cold water over your wrists
                        🌳 **5-4-3-2-1** - Name 5 things you see, 4 you feel, 3 you hear...
                        ☕ **Warm drink** - Hold something warm and focus on the sensation
                        
                        > *"This feeling is temporary. You've survived 100% of your bad days."*
                        """)
                
                elif emotion in ["Sad", "Lonely", "Empty"]:
                    with st.expander("💙 Gentle Comfort", expanded=True):
                        st.markdown("""
                        **Be kind to yourself right now. Here's what helps:**
                        
                        🤗 **Self-compassion break** - Place hand on heart: "This is hard. I'm not alone."
                        📞 **Reach out** - Text or call one person you trust
                        🧣 **Cozy moment** - Wrap yourself in something soft, make tea
                        🎧 **Comfort media** - Put on a familiar show or song that feels safe
                        🌙 **Permission to rest** - You don't have to be productive today
                        
                        > *"You are allowed to feel sad. You are still worthy of love and connection."*
                        """)
                
                elif emotion in ["Angry", "Frustrated"]:
                    with st.expander("🔥 Release Tension", expanded=True):
                        st.markdown("""
                        **Your anger is valid. Here's how to channel it:**
                        
                        🏃 **Physical release** - 1 minute of jumping jacks or shaking your body
                        ✍️ **Write it out** - Type everything you're angry about, then delete it
                        🧊 **Cool down** - Hold an ice cube or splash cold water on your face
                        🗣️ **Name it** - Say out loud: "I am angry because..." 
                        🚶 **Change scenery** - Step outside for 2 minutes
                        
                        > *"Anger is a messenger. Listen to what it's telling you, then release it."*
                        """)
                
                elif emotion in ["Tired"]:
                    with st.expander("😴 Rest & Recharge", expanded=True):
                        st.markdown("""
                        **You're running on empty. Here's how to refill:**
                        
                        ⏸️ **Guilt-free pause** - Rest is productive. Do nothing for 5 minutes.
                        💤 **Power nap** - 20 minutes max, set an alarm
                        🧘 **Body scan** - Close your eyes, notice tension, breathe into it
                        🍵 **Hydrate** - Drink a full glass of water
                        🌿 **Low stimulation** - Dim lights, silence notifications
                        
                        > *"You are not a machine. Rest is not a reward for exhaustion—it's a necessity."*
                        """)
                
                elif emotion in ["Guilty", "Ashamed"]:
                    with st.expander("🕊️ Self-Forgiveness", expanded=True):
                        st.markdown("""
                        **You deserve compassion. Try this:**
                        
                        💬 **Talk to yourself like a friend** - What would you say to someone you love?
                        📝 **Write a forgiveness letter** - To yourself, you don't have to send it
                        🌅 **Fresh start** - Tomorrow is new. This moment is new.
                        🤝 **Connect** - Shame thrives in secrecy. Share with someone safe.
                        
                        > *"You are human. You are learning. You are enough."*
                        """)
                
                elif emotion in ["Okay", "Neutral"]:
                    with st.expander("🌱 Gentle Check-In", expanded=True):
                        st.markdown("""
                        **You're feeling okay. That's perfectly fine. Here's a gentle check-in:**
                        
                        💭 **What do you need right now?** (Rest? Connection? Movement? Silence?)
                        🎯 **What's one tiny step you can take?**
                        🌟 **What's one small thing that went well today?**
                        📖 **Read this:** "You don't have to feel amazing every day. 'Okay' is enough."
                        
                        > *"Peace is not the absence of chaos, but the presence of calm in the midst of it."*
                        """)
                
                else:
                    with st.expander("🌱 Check-In", expanded=True):
                        st.markdown("""
                        **Take a moment with yourself:**
                        
                        💭 **What do I need right now?** (Rest? Connection? Movement? Silence?)
                        🎯 **What's one tiny step I can take?**
                        🤔 **If I felt better, what would be different?**
                        
                        > *"Small steps are still progress."*
                        """)
    
    # Show recent entries at the bottom (collapsible)
    st.divider()
    with st.expander("📋 Your Recent Journal Entries", expanded=False):
        df = load_log()
        if not df.empty:
            recent_entries = df.sort_values(by="date", ascending=False).head(5)
            for _, row in recent_entries.iterrows():
                mood = row["mood"]
                emoji = EMOTION_DATA.get(mood, {}).get("emoji", "📝")
                
                # Source icon
                if row["source"] == "crisis":
                    source_icon = "🚨"
                elif row["source"] == "ai":
                    source_icon = "🤖"
                else:
                    source_icon = "📝"
                
                st.markdown(f"**{emoji} {mood}** {source_icon} • {row['date']}")
                st.caption(row["note"][:100] + "..." if len(row["note"]) > 100 else row["note"])
                st.divider()
        else:
            st.info("No journal entries yet. Write your first entry above!")

# ---------- PAGE 2: HISTORY ----------
elif page == "📊 History":
    st.title("📊 Your Mood History")
    
    df = load_log()
    if df.empty:
        st.info("No entries yet. Start by journaling!")
    else:
        # Convert date column
        df["date"] = pd.to_datetime(df["date"])
        
        # Filter by date range
        col1, col2 = st.columns(2)
        with col1:
            filter_option = st.selectbox(
                "Show",
                ["All time", "Last 7 days", "Last 30 days", "This month"],
                index=0
            )
        
        # Apply date filter
        filtered_df = df.copy()
        if filter_option == "Last 7 days":
            cutoff = pd.Timestamp.now() - pd.Timedelta(days=7)
            filtered_df = filtered_df[filtered_df["date"] >= cutoff]
        elif filter_option == "Last 30 days":
            cutoff = pd.Timestamp.now() - pd.Timedelta(days=30)
            filtered_df = filtered_df[filtered_df["date"] >= cutoff]
        elif filter_option == "This month":
            filtered_df = filtered_df[filtered_df["date"].dt.month == pd.Timestamp.now().month]
        
        with col2:
            source_filter = st.selectbox(
                "Type",
                ["All entries", "Journal only"],
                index=0
            )
        
        if source_filter == "Journal only":
            filtered_df = filtered_df[filtered_df["source"] == "ai"]
        
        # Sort by date
        filtered_df = filtered_df.sort_values("date", ascending=False)
        
        # Metrics
        st.subheader("Overview")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total entries", len(filtered_df))
        with col2:
            if not filtered_df.empty:
                avg_score = filtered_df["score"].mean()
                st.metric("Average mood", f"{avg_score:.1f}/5")
        with col3:
            if not filtered_df.empty:
                most_common = filtered_df["mood"].mode()[0] if not filtered_df["mood"].mode().empty else "N/A"
                emoji = EMOTION_DATA.get(most_common, {}).get("emoji", "")
                st.metric("Most frequent", f"{emoji} {most_common}")
        with col4:
            if not filtered_df.empty:
                today_count = len(filtered_df[filtered_df["date"].dt.date == date.today()])
                st.metric("Today", today_count)
        
        # Mood trend chart
        st.subheader("Mood Trend")
        chart_df = filtered_df.sort_values("date")
        if not chart_df.empty:
            st.line_chart(chart_df.set_index("date")["score"])
        
        # Emotion distribution
        st.subheader("Emotion Distribution")
        mood_counts = filtered_df["mood"].value_counts().head(8)
        
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
        for _, row in filtered_df.head(10).iterrows():
            with st.container():
                col1, col2 = st.columns([1, 5])
                with col1:
                    mood = row["mood"]
                    emoji = EMOTION_DATA.get(mood, {}).get("emoji", "📝")
                    
                    if row["source"] == "crisis":
                        source_icon = "🚨"
                    else:
                        source_icon = "🤖"
                    
                    st.markdown(f"**{emoji}**")
                    st.caption(f"{source_icon}")
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

# ---------- PAGE 3: SELF-CARE ----------
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
            "What small moment
