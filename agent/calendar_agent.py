# agent/calendar_agent.py
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import tool
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.messages import HumanMessage, AIMessage
from typing import List, Optional
from datetime import datetime, timedelta
import requests
import os

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

@tool
def check_calendar_availability(start_time: str, end_time: str) -> dict:
    """Check calendar availability between two datetime strings in ISO format."""
    response = requests.get(
        f"{BACKEND_URL}/availability",
        params={"start": start_time, "end": end_time}
    )
    return response.json()

@tool
def book_appointment(summary: str, start_time: str, end_time: str, 
                    description: Optional[str] = None, 
                    attendees: Optional[List[str]] = None) -> dict:
    """Book an appointment on the calendar with given details."""
    event = {
        "summary": summary,
        "start": start_time,
        "end": end_time,
        "description": description,
        "attendees": attendees or []
    }
    response = requests.post(f"{BACKEND_URL}/events", json=event)
    if response.status_code == 200:
        event_details = response.json()
        return {
            "status": "success",
            "message": f"Meeting booked successfully. You can view it here: {event_details['htmlLink']}",
            "link": event_details['htmlLink']
        }
    return {"status": "error", "message": "Failed to book meeting"}

@tool
def list_events(time_min: Optional[str] = None, time_max: Optional[str] = None, q: Optional[str] = None) -> dict:
    """List calendar events, optionally filtered by time range or search query."""
    params = {}
    if time_min:
        params["time_min"] = time_min
    if time_max:
        params["time_max"] = time_max
    if q:
        params["q"] = q
    response = requests.get(f"{BACKEND_URL}/events", params=params)
    return response.json()

@tool
def update_event(event_id: str, summary: Optional[str] = None, start: Optional[str] = None, end: Optional[str] = None,
                 description: Optional[str] = None, attendees: Optional[List[str]] = None) -> dict:
    """Update an event's details."""
    event = {
        "summary": summary,
        "start": start,
        "end": end,
        "description": description,
        "attendees": attendees
    }
    response = requests.patch(f"{BACKEND_URL}/events/{event_id}", json=event)
    return response.json()

@tool
def delete_event(event_id: str) -> dict:
    """Delete (cancel) an event."""
    response = requests.delete(f"{BACKEND_URL}/events/{event_id}")
    return response.json()

@tool
def reschedule_event(event_id: str, start: str, end: str) -> dict:
    """Reschedule an event to a new time."""
    response = requests.post(f"{BACKEND_URL}/events/{event_id}/reschedule", params={"start": start, "end": end})
    return response.json()

def create_agent():
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if not gemini_api_key:
        raise RuntimeError(
            "GEMINI_API_KEY environment variable is not set. "
            "Please set it in your environment or .env file."
        )
    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-flash-latest",
        temperature=0,
        google_api_key=gemini_api_key
    )
    tools = [
        check_calendar_availability,
        book_appointment,
        list_events,
        update_event,
        delete_event,
        reschedule_event
    ]
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a helpful calendar assistant that helps users book, view, update, and cancel appointments.
You can show all meetings for any date when asked, such as "show all the meetings tomorrow".
Always be polite and confirm details before booking.
Today's date is {current_date}."""),
        ("placeholder", "{chat_history}"),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
    ])
    
    agent = create_tool_calling_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
    return agent_executor

def format_time_suggestions(busy_slots, start, end):
    # Helper function to suggest available times
    pass
    pass
