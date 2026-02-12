# ---------- SIDEBAR - CLEAN MAC-FRIENDLY NAVIGATION ----------
st.sidebar.markdown("""
<style>
    /* Clean, minimal styling for Mac */
    [data-testid="stSidebar"] {
        background-color: #fafafc;
        padding: 20px 0px;
    }
    
    /* App title */
    .sidebar-title {
        font-size: 28px;
        font-weight: 600;
        color: #1a1e24;
        margin-bottom: 8px;
        letter-spacing: -0.5px;
        padding-left: 20px;
    }
    
    /* BIG DATE STYLING */
    .big-date {
        background: white;
        padding: 20px 20px;
        border-radius: 16px;
        margin: 16px 20px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.02);
        border: 1px solid #f0f0f0;
    }
    .day-name {
        font-size: 18px;
        font-weight: 500;
        color: #5e6772;
        margin-bottom: 4px;
        letter-spacing: -0.2px;
    }
    .day-date {
        font-size: 32px;
        font-weight: 700;
        color: #1a1e24;
        line-height: 1.2;
        letter-spacing: -1px;
    }
    .month-year {
        font-size: 18px;
        font-weight: 500;
        color: #5e6772;
        margin-top: 4px;
    }
    
    /* Clean nav buttons - no borders, no backgrounds */
    .nav-item {
        padding: 10px 20px;
        margin: 2px 0px;
        border-radius: 0px;
        font-weight: 500;
        color: #3a4048;
        transition: all 0.1s;
        display: flex;
        align-items: center;
        gap: 12px;
        border-left: 3px solid transparent;
    }
    .nav-item:hover {
        background-color: #e8eaed;
        border-left: 3px solid #8e98a3;
        color: #1a1e24;
    }
    .nav-item-active {
        background-color: #e1f0fa;
        border-left: 3px solid #1a73e8 !important;
        color: #1a73e8;
        font-weight: 600;
    }
    .nav-icon {
        font-size: 20px;
        width: 28px;
        text-align: center;
    }
    .nav-label {
        font-size: 16px;
    }
    
    /* Stats card */
    .stats-card {
        background: white;
        padding: 16px 20px;
        border-radius: 12px;
        margin: 8px 20px;
        border: 1px solid #f0f0f0;
    }
    .stats-label {
        font-size: 14px;
        color: #5e6772;
        margin-bottom: 4px;
    }
    .stats-number {
        font-size: 28px;
        font-weight: 700;
        color: #1a1e24;
    }
    
    /* Divider */
    .sidebar-divider {
        margin: 16px 20px;
        border-top: 1px solid #e8eaed;
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

# Navigation options
nav_items = [
    {"icon": "📝", "label": "Journal", "id": "journal"},
    {"icon": "🤖", "label": "AI Analyzer", "id": "ai"},
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
            use_container_width=True,
            help=f"Go to {item['label']}"
        ):
            st.session_state.current_page = item["id"]
            st.rerun()

# Quick stats
st.sidebar.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)

df = load_log()
if not df.empty:
    today_entries = df[df["date"] == today.isoformat()]
    
    st.sidebar.markdown('<div class="stats-card">', unsafe_allow_html=True)
    st.sidebar.markdown('<div class="stats-label">Today's entries</div>', unsafe_allow_html=True)
    st.sidebar.markdown(f'<div class="stats-number">{len(today_entries)}</div>', unsafe_allow_html=True)
    
    if not today_entries.empty:
        latest_mood = today_entries.iloc[-1]["mood"]
        emoji = EMOTION_DATA.get(latest_mood, {}).get("emoji", "📝")
        st.sidebar.markdown(f'<div style="margin-top: 12px; font-size: 16px;">Latest: {emoji} {latest_mood}</div>', unsafe_allow_html=True)
    st.sidebar.markdown('</div>', unsafe_allow_html=True)
else:
    st.sidebar.markdown('<div class="stats-card">', unsafe_allow_html=True)
    st.sidebar.markdown('<div class="stats-label">Welcome!</div>', unsafe_allow_html=True)
    st.sidebar.markdown('<div style="font-size: 16px; margin-top: 8px;">Start your first entry ✨</div>', unsafe_allow_html=True)
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
    "ai": "🤖 AI Analyzer", 
    "history": "📊 History",
    "selfcare": "🧰 Self-Care",
    "crisis": "🆘 Crisis Help"
}
page = page_map[st.session_state.current_page]
