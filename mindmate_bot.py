import streamlit as st
import pyrebase
import ollama
import datetime
import pandas as pd
import time
import json
import httpx
client = httpx.Client(verify=False)
# Apply custom styles

def apply_custom_styles():
    st.markdown("""
    <style>
    /* -------- Background Color Update -------- */
    .stApp {
        background-color: #ffe5bd !important; /* New background color */
    }

    /* -------- Sidebar Styling -------- */
    [data-testid="stSidebar"] {
        background-color: #d2b48c;
        color: #000000 !important; /* Black text */
    }

    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3, 
    [data-testid="stSidebar"] h4, [data-testid="stSidebar"] h5, [data-testid="stSidebar"] h6, 
    [data-testid="stSidebar"] .stMarkdown, [data-testid="stSidebar"] label, 
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] span {
        color: #000000 !important; /* BLACK outside buttons */
        font-weight: normal !important;
    }

    /* -------- Main Content Text -------- */
    h1, h2, h3, h4, h5, h6, p, label, .stMarkdown, .stTextInput, 
    .stSelectbox, .stTextArea, .stForm, span {
        color: #000000 !important; /* BLACK text everywhere outside buttons */
        font-weight: normal !important;
    }

    /* -------- BUTTON STYLING -------- */
    .stButton > button, .stForm button {
        background-color: #0e453d !important; /* Dark green button */
        color: #ffffff !important;            /* WHITE button text */
        -webkit-text-fill-color: #ffffff !important; /* Force white text */
        font-weight: 900 !important;          /* Super bold */
        font-size: 16px !important;           /* Bigger for visibility */
        text-shadow: none !important;         /* Remove fading */
        border-radius: 12px !important;
        padding: 12px 22px !important;
        border: none !important;
        opacity: 1 !important;
        filter: none !important;
        letter-spacing: 0.5px !important;
    }

    /* Hover State */
    .stButton > button:hover, .stForm button:hover {
        background-color: #092e28 !important; /* Darker green */
        color: #ffffff !important;            /* Keep white text */
        -webkit-text-fill-color: #ffffff !important;
    }

    /* Disabled Buttons */
    .stButton > button:disabled, .stForm button:disabled {
        background-color: #0e453d !important;
        color: #ffffff !important;            /* WHITE text */
        -webkit-text-fill-color: #ffffff !important; /* Force white */
        font-weight: 900 !important;
        opacity: 0.9 !important;
        filter: none !important;
        pointer-events: none !important;
    }

    /* Fix deeply nested button span (Streamlit internal override) */
    .stButton > button span, .stForm button span {
        color: #ffffff !important;            /* WHITE text */
        -webkit-text-fill-color: #ffffff !important;
        font-weight: 900 !important;
    }

    /* -------- Dropdown Styling -------- */
    [data-testid="stSelectbox"] > div {
        background-color: #ffffff !important;
        color: #000000 !important;            /* BLACK dropdown text */
        border-radius: 8px;
        border: 1px solid #90a4ae;
        padding: 5px;
    }

    [data-testid="stSelectbox"] div span {
        color: #000000 !important;            /* BLACK dropdown options */
    }

    /* -------- Input Fields -------- */
    input, textarea {
        background-color: #ffffff !important;
        color: #000000 !important;            /* BLACK input text */
        border: 1px solid #b0bec5;
        border-radius: 10px;
        padding: 8px;
    }

    /* -------- Info, Success, and Error Messages -------- */
    .stSuccess, .stError, .stInfo {
        border-radius: 10px;
        padding: 10px;
        color: #000000 !important;            /* BLACK text */
    }

     /* -------- Fix Eye Icon Alignment in Password Field -------- */
input[type="password"] {
    padding-right: 50px !important; /* Space for the icon */
    height: 48px !important; /* Ensures input field height consistency */
    border-radius: 10px !important; /* Match the border radius */
}

.stTextInput div[data-baseweb="input"] {
    display: flex !important;
    align-items: center !important;
    position: relative !important;
}

/* Eye icon button container */
.stTextInput div[data-baseweb="input"] button {
    position: absolute !important;
    right: 0px !important;
    top: 0px !important;
    bottom: 0px !important;
    width: 50px !important;  /* Adjust width to fit the icon */
    height: 100% !important; /* Fill the height of the input field */
    display: flex !important;
    justify-content: center !important;
    align-items: center !important;
    border: none !important;
    background-color: #0e453d !important; /* Match existing button color */
    border-radius: 0 10px 10px 0 !important; /* Match input corners */
    cursor: pointer !important;
    padding: 0 !important;
}

/* Make the eye icon larger and visible */
.stTextInput div[data-baseweb="input"] button svg {
    width: 22px !important;
    height: 22px !important;
    fill: #ffffff !important; /* White eye icon */
}
                
    </style>
    """, unsafe_allow_html=True)


# Call this function at the start of your app
apply_custom_styles()

# ----------------- Firebase Configuration -----------------

with open('firebase.json', 'r') as f: 
    firebase_config = json.load(f)['firebaseConfig']
    
firebase = pyrebase.initialize_app(firebase_config)
auth = firebase.auth()

# ----------------- Helper Functions -----------------

def generate_chat_name(messages, chat_id):
    user_messages = [msg["content"]
                     for msg in messages if msg["role"] == "user"]
    timestamp = datetime.datetime.strptime(
        chat_id, "%Y-%m-%d %H:%M:%S").strftime("%m/%d %H:%M")
    return f"{user_messages[0][:20]}{'...' if len(user_messages[0]) > 20 else ''} - {timestamp}" if user_messages else f"New Chat - {timestamp}"


def clear_conversation_history():
    if "chats" not in st.session_state:
        st.session_state["chats"] = {}
    chat_id = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.session_state["chats"][chat_id] = {
        "name": f"New Chat - {chat_id}", "messages": []}
    st.session_state["current_chat"] = chat_id
    st.session_state.pop("user_input", None)  # Clear input field

# ----------------- Account Functions -----------------

def signup(email, password):
    try:
        auth.create_user_with_email_and_password(email, password)
        st.success(f"✅ Account created for {email}. Please log in.")
        st.rerun()
    except Exception as e:
        st.error(f"🚫 Sign-up failed: {str(e)}")


def login(email, password):
    try:
        user = auth.sign_in_with_email_and_password(email, password)
        if st.session_state.get('current_user_email') != email:
            st.session_state["chats"] = {}
            clear_conversation_history()
        st.session_state['user'] = user
        st.session_state['current_user_email'] = email
        st.success(f"✅ Logged in as {email}")
        st.rerun()
    except Exception as e:
        st.error(f"🚫 Login failed: {str(e)}")

def logout():
    if 'user' in st.session_state:
        del st.session_state['user']
        del st.session_state['current_user_email']
        st.session_state["chats"] = {}
        clear_conversation_history()
        st.success("✅ Logged out successfully!")
        st.rerun()

# ----------------- Breathing Exercise -----------------

def breathing_exercise():
    st.subheader("🧘 Breathing Exercise")
    duration = st.slider("Select duration (seconds):", 10, 60, 30, 5)
    st.write("Follow the breathing pattern below:")
    placeholder = st.empty()

    for _ in range(duration // 4):
        placeholder.markdown("### 🌬️ **Inhale...**")
        time.sleep(2)
        placeholder.markdown("### 😮‍💨 **Hold...**")
        time.sleep(1)
        placeholder.markdown("### 🌬️ **Exhale...**")
        time.sleep(2)
    placeholder.empty()
    st.success("✅ Great job! Feel the calmness. 🌿")


# ----------------- Guided Meditation -----------------
def guided_meditation():
    st.subheader("🧘‍♂️ Guided Meditation")
    meditations = {
        "Stress Relief (3 mins)": {"message": "🌱 Take slow, deep breaths. Let go of tension with each exhale.", "duration": 3},
        "Sleep Relaxation (5 mins)": {"message": "😴 Relax your body, starting from your toes to your head. Drift into calm.", "duration": 5},
        "Focus Boost (2 mins)": {"message": "💡 Center your mind on your breath. Each inhale brings clarity.", "duration": 2}
    }

    choice = st.selectbox("Choose a meditation:", list(
        meditations.keys()), key="meditation_choice")

    if st.button("▶️ Start Meditation", key="start_meditation"):
        meditation = meditations[choice]
        st.info(meditation["message"])

        with st.spinner(f"Meditation in progress... ({meditation['duration']} minutes)"):
            total_seconds = meditation["duration"] * 60
            countdown_placeholder = st.empty()

            for remaining in range(total_seconds, 0, -1):
                mins, secs = divmod(remaining, 60)
                countdown_placeholder.markdown(
                    f"⏳ **Time remaining:** {mins:02d}:{secs:02d}")
                time.sleep(1)
            countdown_placeholder.empty()

        st.success("✅ Meditation complete! 🌼 Take a deep breath.")


# ----------------- Mood Tracker -----------------
if "mood_data" not in st.session_state:
    st.session_state["mood_data"] = []


def submit_mood(mood):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    st.session_state["mood_data"].append({"Time": timestamp, "Mood": mood})
    st.success(f"✅ Mood '{mood}' recorded!")


def show_mood_chart():
    if st.session_state["mood_data"]:
        df = pd.DataFrame(st.session_state["mood_data"])
        mood_map = {"Happy": 5, "Excited": 4,
                    "Neutral": 3, "Anxious": 2, "Sad": 1}
        df["Mood Score"] = df["Mood"].map(mood_map)
        df["Time"] = pd.to_datetime(df["Time"])
        df = df.sort_values("Time")
        st.line_chart(df.set_index("Time")[
                      "Mood Score"], use_container_width=True)
    else:
        st.info("ℹ️ No mood data recorded yet. Start tracking to see trends!")


# ----------------- Affirmations -----------------
if "favorite_affirmations" not in st.session_state:
    st.session_state["favorite_affirmations"] = []

themes = {
    "Anxiety Relief": ["You are safe and in control.", "This feeling is temporary. Breathe deeply."],
    "Motivation": ["You are capable of amazing things!", "Small steps lead to big achievements."],
    "Sleep": ["You deserve rest and peace.", "Let go of today, tomorrow is a new day."],
    "Stress Management": ["Breathe in calm, breathe out stress.", "You’ve handled tough things before—you’ve got this!"]
}


def show_affirmations(theme):
    st.subheader(f"🌟 {theme} Affirmations")
    available_affirmations = [a for a in themes[theme]
                              if a not in st.session_state["favorite_affirmations"]]

    if not available_affirmations:
        st.info("🎉 You've saved all affirmations in this theme!")
    else:
        for affirmation in available_affirmations[:2]:
            st.markdown(f"💬 *{affirmation}*")
            if st.button(f"❤️ Save", key=f"save_{theme}_{affirmation}"):
                st.session_state["favorite_affirmations"].append(affirmation)
                st.success("✅ Added to favorites!")
                st.rerun()


def show_favorites():
    st.subheader("💖 Your Favorite Affirmations")
    if st.session_state["favorite_affirmations"]:
        for fav in st.session_state["favorite_affirmations"]:
            st.markdown(f"✅ *{fav}*")
    else:
        st.info("ℹ️ No favorites saved yet.")


# ----------------- Chatbot -----------------
if "chats" not in st.session_state:
    st.session_state["chats"] = {}

if "current_chat" not in st.session_state:
    clear_conversation_history()


def get_response(prompt):
    prompt_lower = prompt.lower().strip()
    if any(q in prompt_lower for q in ["what do i call you", "your name", "what's your name"]):
        return "You can call me your CalmBuddy. 😊"
    if any(q in prompt_lower for q in ["how do i use you", "how can i use you"]):
        return "I am your CalmBuddy. I can answer mental health questions, track your mood, and offer coping strategies. 💙"
    try:
        response = ollama.chat(model="llama2", messages=[
                               {"role": "user", "content": prompt}])
        return response['message']['content']
    except Exception as e:
        return f"⚠️ Error generating response: {str(e)}"


def generate_response(user_input):
    chat_id = st.session_state["current_chat"]
    messages = st.session_state["chats"][chat_id]["messages"]
    messages.append({"role": "divider", "content": "---"})
    messages.append({"role": "user", "content": user_input})
    ai_response = get_response(user_input)
    messages.append({"role": "assistant", "content": ai_response})
    if st.session_state["chats"][chat_id]["name"].startswith("New Chat"):
        st.session_state["chats"][chat_id]["name"] = generate_chat_name(
            messages, chat_id)
    return ai_response


# ----------------- User Interface -----------------
st.title("💬 CalmBuddy: Your Mental Health Companion")

def authentication_page():
    st.header("🔑 Welcome to CalmBuddy")
    auth_option = st.radio("Choose an option:", [
                           "Login", "Sign Up"], horizontal=True)

    with st.form(key="auth_form"):
        email = st.text_input("📧 Email", placeholder="Enter your email")
        password = st.text_input(
            "🔒 Password", type="password", placeholder="Enter your password")

        if auth_option == "Sign Up":
            confirm_password = st.text_input(
                "🔑 Confirm Password", type="password", placeholder="Re-enter your password")
            submit_btn = st.form_submit_button("📝 Sign Up")

            if submit_btn:
                if password != confirm_password:
                    st.error("🚫 Passwords do not match!")
                elif len(password) < 6:
                    st.error("🚫 Password must be at least 6 characters.")
                else:
                    signup(email, password)

        else:  # Login form
            submit_btn = st.form_submit_button("🔓 Login")
            if submit_btn:
                if not email or not password:
                    st.error("🚫 Please fill out both fields.")
                else:
                    login(email, password)


# Use this function where the login condition is checked
if 'user' not in st.session_state:
    authentication_page()
else:
    with st.sidebar:
        st.success(f"✅ Logged in as: {st.session_state['current_user_email']}")

        if st.button("➕ New Chat"):
            clear_conversation_history()
            st.rerun()

        st.subheader("📊 Mood Tracker")
        mood = st.selectbox("How are you feeling today?", [
                            "Happy", "Excited", "Neutral", "Anxious", "Sad"])
        if st.button("Submit Mood"):
            submit_mood(mood)
        show_mood_chart()

        st.subheader("🧘 Breathing & Meditation")
        if st.button("Start Breathing Exercise"):
            breathing_exercise()
        if st.button("Start Guided Meditation"):
            guided_meditation()

        st.subheader("🌿 Personalized Affirmations")
        theme = st.selectbox("Choose a theme:", list(themes.keys()))
        show_affirmations(theme)
        show_favorites()

        st.subheader("📜 Previous Chats")
        for chat_id, chat_data in sorted(st.session_state["chats"].items(), reverse=True):
            if st.button(chat_data["name"], key=f"chat_{chat_id}"):
                st.session_state["current_chat"] = chat_id
                st.session_state.pop("user_input", None)
                st.rerun()

        if st.button("🚪 Logout"):
            logout()

# ✅ Display chat messages after login
if 'user' in st.session_state:
    chat_id = st.session_state["current_chat"]
    for msg in st.session_state["chats"][chat_id]["messages"]:
        st.markdown(
            "---" if msg['role'] == "divider" else f"**{'👤 You' if msg['role'] == 'user' else '🤖 CalmBuddy'}:** {msg['content']}"
        )

    # Initialize the session state for preset messages
    if "preset_message" not in st.session_state:
        st.session_state.preset_message = ""

    # 🔤 Chat form with preset message handling
    with st.form(key="chat_form"):
        current_message = st.session_state.preset_message or ""
        user_message = st.text_input(
            "💭 How can I help you today?",
            value=current_message,
            key="user_input"
        )
        submit_button = st.form_submit_button("Send")

        # 🔄 Clear preset message after sending
        if submit_button:
            st.session_state.preset_message = ""

    # 📝 Process chat input
    if submit_button and user_message.strip():
        with st.spinner("🤔 Thinking..."):
            generate_response(user_message.strip())
            st.rerun()

    # ⬇️ Quick access buttons BELOW the chat form
    st.markdown("---")  # Separator between chat form and quick access section
    # 🔥 Added heading above quick access buttons
    st.subheader("🚀 Quick Access")

    # CSS style to improve button visibility and reduce spacing
    st.markdown("""
    <style>
    div[data-testid="column"] > div {
        margin-bottom: -35px !important;  /* Reduce vertical space between buttons */
        padding: 0px !important;
    }
    button[kind="secondary"] {
        background-color: #0e453d !important; /* Green buttons */
        color: #ffffff !important;             /* White text for visibility */
        font-weight: bold !important;
        border-radius: 10px !important;
        padding: 6px 10px !important;         /* Adjusted padding for compactness */
        font-size: 13px !important;           /* Legible font size */
        border: none !important;
    }
    button[kind="secondary"]:hover {
        background-color: #388e3c !important; /* Darker green on hover */
    }
    </style>
    """, unsafe_allow_html=True)

    # 🧘‍♀️ Well-being & Emotional Support
    st.markdown("### 🧘‍♀️ Well-being & Emotional Support")
    col1, col2, col3, col4 = st.columns(4, gap="small")

    with col1:
        if st.button("🧘 Mindfulness"):
            st.session_state.preset_message = "Guide me through mindfulness exercises"
            st.rerun()

    with col2:
        if st.button("🌬️ Breathing"):
            st.session_state.preset_message = "Start a quick breathing exercise"
            st.rerun()

    with col3:
        if st.button("💬 Affirmations"):
            st.session_state.preset_message = "I need a positive affirmation"
            st.rerun()

    with col4:
        if st.button("🙏 Gratitude"):
            st.session_state.preset_message = "Help me practice gratitude"
            st.rerun()

    # 🧩 Productivity & Focus
    st.markdown("### 🧩 Productivity & Focus")
    col1, col2, col3 = st.columns(3, gap="small")

    with col1:
        if st.button("🎯 Focus Tips"):
            st.session_state.preset_message = "Tips to improve my focus"
            st.rerun()

    with col2:
        if st.button("⏳ Procrastination"):
            st.session_state.preset_message = "Help me with procrastination"
            st.rerun()

    with col3:
        if st.button("⚡ Energy Boost"):
            st.session_state.preset_message = "How to boost my energy?"
            st.rerun()

    # 🛌 Sleep & Relaxation
    st.markdown("### 🛌 Sleep & Relaxation")
    col1, col2 = st.columns(2, gap="small")

    with col1:
        if st.button("🛏️ Bedtime Routine"):
            st.session_state.preset_message = "Guide me through a bedtime routine"
            st.rerun()

    with col2:
        if st.button("🎶 Relaxing Sounds"):
            st.session_state.preset_message = "Play calming sounds"
            st.rerun()

    # 💪 Motivation & Positivity
    st.markdown("### 💪 Motivation & Positivity")
    col1, col2 = st.columns(2, gap="small")

    with col1:
        if st.button("🔥 Motivational Quote"):
            st.session_state.preset_message = "Give me a motivational quote"
            st.rerun()

    with col2:
        if st.button("📈 Goal Setting"):
            st.session_state.preset_message = "Help me set achievable goals"
            st.rerun()

    # 🚑 Crisis Support
    st.markdown("### 🚑 Crisis Support")
    if st.button("🚨 Emergency Help"):
        st.session_state.preset_message = "I need immediate help"
        st.rerun()

    # 📚 Resources Section
    st.markdown("---")
    st.subheader("📚 Resources")
    st.markdown(
        "If you're in immediate danger or need urgent help, please call emergency services (911 in the U.S.).")
    st.markdown("✅ **How do I get help?**")
    st.markdown("- Reach out to a trusted friend or family member.\n- Contact a mental health professional.\n- Use the resources below for immediate support.")
    st.markdown(
        "🚑 **National Suicide Prevention Lifeline (USA):** Call or text **988** for 24/7 free, confidential support.")
    st.markdown(
        "🌐 **Crisis Text Line:** Text **HELLO** to **741741** to connect with a crisis counselor.")
    st.markdown(
        "📞 **International Helplines:** Visit [findahelpline.com](https://findahelpline.com/) for support in your country.")

# 🚫 Hide everything until user logs in
else:
    st.warning("🔒 Please log in to start chatting with CalmBuddy.")
