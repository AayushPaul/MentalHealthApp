import streamlit as st
import pyrebase
import base64
import ollama
import datetime
import json

# ----------------- Firebase Configuration -----------------
with open('firebase.json', 'r') as f: 
    firebase_config = json.load(f)['firebaseConfig']

firebase = pyrebase.initialize_app(firebase_config)
auth = firebase.auth()

# ----------------- Background Image Setup -----------------

def get_base64(background):
    with open(background, "rb") as f:
        return base64.b64encode(f.read()).decode()


bin_str = get_base64("background.png")

st.markdown(f"""
    <style>
        .main {{
            background-image: url("data:image/png;base64,{bin_str}");
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
        }}
    </style>
""", unsafe_allow_html=True)

# ----------------- Helper Functions -----------------


def generate_chat_name(messages, chat_id):
    """Generate chat name using the first user message + short date."""
    user_messages = [msg["content"]
                     for msg in messages if msg["role"] == "user"]
    timestamp = datetime.datetime.strptime(
        chat_id, "%Y-%m-%d %H:%M:%S").strftime("%m/%d %H:%M")

    if user_messages:
        base_name = user_messages[0][:20].strip()  # Truncate to 20 chars
        name = f"{base_name}{'...' if len(user_messages[0]) > 20 else ''} - {timestamp}"
    else:
        name = f"New Chat - {timestamp}"

    return name


def clear_conversation_history():
    """Start a new empty chat session and clear input."""
    if "chats" not in st.session_state:
        st.session_state["chats"] = {}

    chat_id = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.session_state["chats"][chat_id] = {
        "name": f"New Chat - {chat_id}", "messages": []
    }
    st.session_state["current_chat"] = chat_id
    st.session_state.pop("user_input", None)  # Clear input field


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


# ----------------- Chatbot Functions -----------------
if "chats" not in st.session_state:
    st.session_state["chats"] = {}

if "current_chat" not in st.session_state:
    clear_conversation_history()


def get_response(prompt):
    """Respond to special prompts or use Ollama for others."""
    prompt_lower = prompt.lower().strip()

    call_you_prompts = ["what do i call you",
                        "what should i call you", "your name", "what's your name"]
    how_to_use_prompts = ["how do i use you",
                          "how can i use you", "how to use", "help me use you"]

    if any(q in prompt_lower for q in call_you_prompts):
        return "You can call me your CalmBuddy. 😊"

    if any(q in prompt_lower for q in how_to_use_prompts):
        return "I am your CalmBuddy. I can answer any questions about mental health and provide support whenever you need it. 💙"

    try:
        response = ollama.chat(model="llama3.1:8b", messages=[
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
st.title("💬 Mental Health Support Agent")

# 🔐 Login/Signup Interface
if 'user' not in st.session_state:
    st.header("🔑 Login or Sign Up")
    tab1, tab2 = st.tabs(["Login", "Sign Up"])

    with tab1:
        login_email = st.text_input("📧 Email", key="login_email")
        login_password = st.text_input(
            "🔒 Password", type="password", key="login_password")
        if st.button("🔓 Login"):
            login(login_email, login_password)

    with tab2:
        signup_email = st.text_input("📧 Email", key="signup_email")
        signup_password = st.text_input(
            "🔒 Password", type="password", key="signup_password")
        if st.button("📝 Sign Up"):
            signup(signup_email, signup_password)

# ✅ Chatbot Interface after login
else:
    with st.sidebar:
        st.success(f"✅ Logged in as: {st.session_state['current_user_email']}")

        if st.button("➕ New Chat"):
            clear_conversation_history()
            st.rerun()

        st.subheader("📜 Previous Chats")
        for chat_id, chat_data in sorted(st.session_state["chats"].items(), reverse=True):
            chat_name = chat_data["name"]
            if st.button(chat_name, key=f"chat_{chat_id}"):
                st.session_state["current_chat"] = chat_id
                st.session_state.pop("user_input", None)
                st.rerun()

        if st.button("🚪 Logout"):
            logout()

    # Main Chat Section
    st.subheader("💬 Chat with CalmBuddy")

    chat_id = st.session_state["current_chat"]
    for msg in st.session_state["chats"][chat_id]["messages"]:
        if msg['role'] == "divider":
            st.markdown("---")
        else:
            role = "👤 You" if msg['role'] == "user" else "🤖 CalmBuddy"
            st.markdown(f"**{role}:** {msg['content']}")

    with st.form(key="chat_form"):
        user_message = st.text_input(
            "💭 How can I help you today?", key="user_input", value="")
        if st.form_submit_button("Send") and user_message.strip():
            with st.spinner("🤔 Thinking..."):
                generate_response(user_message.strip())
                st.rerun()



