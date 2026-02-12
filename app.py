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
api_key = "AIzaSyD5xvU9HFoT3XpogoAoJ3EGR-v35AEbo_Y"
genai.configure(api_key=api_key)

# ---- LOAD GEMINI MODEL ----
model = genai.GenerativeModel("gemini-2.5-flash")

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
        # ---- EXPANDED DANGEROUS CONTENT CHECK ----
        danger_words = [
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
        
        # Check if ANY danger phrase appears
        entry_lower = journal_entry.lower()
        found_danger = any(word in entry_lower for word in danger_words)
        
        if found_danger:
            st.error("""
                🚨 **CRITICAL ALERT - IMMEDIATE HELP NEEDED** 🚨
                
                Your journal entry contains thoughts about harming yourself or others.
                
                **IN SINGAPORE, HELP IS AVAILABLE 24/7:**
                
                📞 **Samaritans of Singapore (SOS):** 1767 (24 hours)
                💬 **SOS Care Text:** 9151 1767 (WhatsApp)
                🌐 **Chat Online:** https://www.sos.org.sg/
                
                🏥 **IMH Mental Health Helpline:** 6389 2222
                🧑‍⚕️ **CHAT (Youth):** 6493 6500 / www.chat.mentalhealth.sg
                
                ⚕️ **Singapore General Hospital:** 6222 3322
                👥 **TOUCHline (Counselling):** 6804 6555
                
                ---
                **Please reach out now. You are not alone. 💛**
                """)
        else:
            st.info("Analyzing your mood... 🤖")

            # ---- IMPROVED PROMPT FOR REAL EMOTIONS ----
            prompt_text = f"""
            You are a highly empathetic mental health assistant and mood analyzer.
            
            Read this journal entry and identify the **specific, real emotion** the person is feeling.
            
            Journal Entry: \"\"\"{journal_entry}\"\"\"
            
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
                response = model.generate_content(prompt_text)
                mood_text = response.text.strip()
                
                # Split into emotion and explanation
                lines = mood_text.split('\n')
                emotion = "Neutral"
                explanation = mood_text
                
                # Extract the emotion word
                for line in lines:
                    if line.lower().startswith("emotion:"):
                        emotion = line.replace("Emotion:", "").replace("emotion:", "").strip()
                        break
                
                # ---- EMOTION MAPPING WITH EMOJIS AND COLORS ----
                emotion_data = {
                    # Positive emotions
                    "Happy": {"emoji": "😊", "color": "success"},
                    "Excited": {"emoji": "🎉", "color": "success"},
                    "Calm": {"emoji": "😌", "color": "success"},
                    "Grateful": {"emoji": "🙏", "color": "success"},
                    "Hopeful": {"emoji": "✨", "color": "success"},
                    
                    # Anxious/Stressed
                    "Anxious": {"emoji": "😰", "color": "warning"},
                    "Stressed": {"emoji": "😫", "color": "warning"},
                    "Overwhelmed": {"emoji": "😩", "color": "warning"},
                    "Scared": {"emoji": "😨", "color": "warning"},
                    
                    # Sad/Lonely
                    "Sad": {"emoji": "😢", "color": "error"},
                    "Lonely": {"emoji": "💔", "color": "error"},
                    "Empty": {"emoji": "🕳️", "color": "error"},
                    "Tired": {"emoji": "😴", "color": "info"},
                    
                    # Angry/Frustrated
                    "Angry": {"emoji": "😠", "color": "error"},
                    "Frustrated": {"emoji": "😤", "color": "error"},
                    
                    # Guilty/Ashamed
                    "Guilty": {"emoji": "😞", "color": "error"},
                    "Ashamed": {"emoji": "😶", "color": "error"},
                }
                
                # Default if emotion not found in mapping
                if emotion in emotion_data:
                    emoji = emotion_data[emotion]["emoji"]
                    color = emotion_data[emotion]["color"]
                else:
                    emoji = "🧠"
                    color = "info"
                
                # ---- DISPLAY EMOTION WITH PROPER COLOR ----
                if color == "success":
                    st.success(f"{emoji} **{emotion}**\n\n{explanation}")
                elif color == "warning":
                    st.warning(f"{emoji} **{emotion}**\n\n{explanation}")
                elif color == "error":
                    st.error(f"{emoji} **{emotion}**\n\n{explanation}")
                else:
                    st.info(f"{emoji} **{emotion}**\n\n{explanation}")
                
                # ---- SAVE TO HISTORY ----
                st.session_state.entries.append(journal_entry)
                st.session_state.moods.append(emotion)

            except Exception as e:
                st.error(f"AI request failed: {e}")

# ---- DISPLAY HISTORY WITH REAL EMOTIONS ----
if st.session_state.entries:
    st.subheader("📖 Journal History")
    
    # Show summary counts
    if st.session_state.moods:
        col1, col2, col3 = st.columns(3)
        happy_count = sum(1 for m in st.session_state.moods if m in ["Happy", "Excited", "Calm", "Grateful", "Hopeful"])
        anxious_count = sum(1 for m in st.session_state.moods if m in ["Anxious", "Stressed", "Overwhelmed", "Scared"])
        sad_count = sum(1 for m in st.session_state.moods if m in ["Sad", "Lonely", "Empty", "Angry", "Frustrated", "Guilty", "Ashamed"])
        
        col1.metric("😊 Positive", happy_count)
        col2.metric("😰 Anxious", anxious_count)
        col3.metric("😢 Distressed", sad_count)
    
    st.divider()
    
    # Display history
    for i in range(len(st.session_state.entries) - 1, -1, -1):
        entry = st.session_state.entries[i]
        emotion = st.session_state.moods[i]
        
        if emotion in emotion_data:
            emoji = emotion_data[emotion]["emoji"]
            color = emotion_data[emotion]["color"]
        else:
            emoji = "📝"
            color = "info"
        
        # Create expander for each entry
        with st.expander(f"{emoji} Entry #{i+1} - {emotion}"):
            st.write(entry)
