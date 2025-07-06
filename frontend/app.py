# frontend/app.py
import sys
from pathlib import Path
import json
from urllib.parse import urlparse

# Add the parent directory to Python path
sys.path.append(str(Path(__file__).parent.parent))

# Load environment variables from .env
from dotenv import load_dotenv
load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")

# Now import from agent
from agent.calendar_agent import create_agent
import streamlit as st
from datetime import datetime

st.title("📅 Calendar Booking Assistant")

def is_valid_calendar_link(url):
    """Check if the URL is a valid Google Calendar link"""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc]) and "calendar.google.com" in result.netloc
    except:
        return False

def display_response(response):
    """Parse and display the agent's response"""
    output = response.get("output", "")
    
    # Try to parse as JSON (for structured responses with links)
    try:
        data = json.loads(output)
        if isinstance(data, dict) and data.get("status") == "success" and is_valid_calendar_link(data.get("link", "")):
            st.markdown(f"✅ **Meeting booked successfully!**")
            st.markdown(f"📅 [View in Calendar]({data['link']})")
            if "message" in data:
                st.markdown(data["message"])
            return
    except json.JSONDecodeError:
        pass
    
    # Fallback to regular text display
    st.markdown(output)

if "agent" not in st.session_state:
    st.session_state.agent = create_agent()
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        content = message["content"]
        if isinstance(content, dict) and content.get("type") == "booking":
            st.markdown(f"✅ **{content.get('summary', 'Meeting')}**")
            st.markdown(f"📅 [View in Calendar]({content['link']})")
            st.markdown(f"🗓️ {content.get('time', '')}")
        else:
            st.markdown(content)

# Handle new input
if prompt := st.chat_input("How can I help you book an appointment?"):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("user"):
        st.markdown(prompt)
    
    with st.chat_message("assistant"):
        try:
            response = st.session_state.agent.invoke({
                "input": prompt,
                "chat_history": st.session_state.messages[:-1],
                "current_date": datetime.now().strftime("%Y-%m-%d")
            })
            # Display the response
            output = response.get("output", "")
            try:
                # Try to parse structured booking response
                data = json.loads(output)
                if isinstance(data, dict) and data.get("status") == "success" and is_valid_calendar_link(data.get("link", "")):
                    # Format booking confirmation
                    booking_message = {
                        "type": "booking",
                        "summary": data.get("summary", "Meeting"),
                        "link": data["link"],
                        "time": data.get("time", ""),
                        "message": data.get("message", "Meeting booked successfully")
                    }
                    st.session_state.messages.append({"role": "assistant", "content": booking_message})
                    
                    st.markdown(f"✅ **{booking_message['summary']}**")
                    st.markdown(f"📅 [View in Calendar]({booking_message['link']})")
                    if booking_message['time']:
                        st.markdown(f"⏰ {booking_message['time']}")
                else:
                    # Regular JSON response
                    st.markdown(output)
                    st.session_state.messages.append({"role": "assistant", "content": output})
            except json.JSONDecodeError:
                # Regular text response
                st.markdown(output)
                st.session_state.messages.append({"role": "assistant", "content": output})
        except Exception as e:
            error_msg = str(e)
            if "ResourceExhausted" in error_msg or "429" in error_msg:
                st.error("🚫 Gemini API quota exceeded. Please try again later or check your API usage limits.")
                st.session_state.messages.append({"role": "assistant", "content": "Sorry, the AI quota has been exceeded. Please try again later."})
            else:
                st.error(f"An error occurred: {error_msg}")
                st.session_state.messages.append({"role": "assistant", "content": f"An error occurred: {error_msg}"})