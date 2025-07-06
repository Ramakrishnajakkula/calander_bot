# backend/main.py
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from datetime import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build
import os
from typing import List, Optional

app = FastAPI()

# Google Calendar setup
SCOPES = ['https://www.googleapis.com/auth/calendar']
SERVICE_ACCOUNT_FILE = os.getenv('GOOGLE_CREDENTIALS_JSON', 'service_account.json')

class Event(BaseModel):
    summary: str
    start: str
    end: str
    attendees: Optional[List[str]] = None
    description: Optional[str] = None

def get_calendar_service():
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    service = build('calendar', 'v3', credentials=creds)
    return service

@app.post("/events")
def create_event(event: Event):
    try:
        service = get_calendar_service()
        event_body = {
            'summary': event.summary,
            'start': {'dateTime': event.start, 'timeZone': 'UTC'},
            'end': {'dateTime': event.end, 'timeZone': 'UTC'},
        }
        if event.description:
            event_body['description'] = event.description
        if event.attendees:
            event_body['attendees'] = [{'email': email} for email in event.attendees]
        
        created_event = service.events().insert(
            calendarId='primary',
            body=event_body
        ).execute()
        
        return {
            "id": created_event['id'],
            "htmlLink": created_event['htmlLink'],  # This is the important part
            "status": "success"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/availability")
def check_availability(start: str, end: str):
    try:
        service = get_calendar_service()
        events_result = service.events().list(
            calendarId='primary',
            timeMin=start,
            timeMax=end,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        return {"busy": [{"start": e['start']['dateTime'], "end": e['end']['dateTime']} 
                        for e in events_result.get('items', [])]}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/events")
def list_events(
    time_min: Optional[str] = Query(None),
    time_max: Optional[str] = Query(None),
    q: Optional[str] = Query(None)
):
    """
    List calendar events. Optionally filter by time range or search query.
    """
    try:
        service = get_calendar_service()
        params = {
            "calendarId": "primary",
            "singleEvents": True,
            "orderBy": "startTime"
        }
        if time_min:
            params["timeMin"] = time_min
        if time_max:
            params["timeMax"] = time_max
        if q:
            params["q"] = q
        events_result = service.events().list(**params).execute()
        return {"events": events_result.get("items", [])}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.patch("/events/{event_id}")
def update_event(event_id: str, event: Event):
    """
    Update an event's details.
    """
    try:
        service = get_calendar_service()
        # Fetch the existing event
        existing = service.events().get(calendarId='primary', eventId=event_id).execute()
        # Update fields
        if event.summary:
            existing['summary'] = event.summary
        if event.start:
            existing['start'] = {'dateTime': event.start, 'timeZone': 'UTC'}
        if event.end:
            existing['end'] = {'dateTime': event.end, 'timeZone': 'UTC'}
        if event.description is not None:
            existing['description'] = event.description
        if event.attendees is not None:
            existing['attendees'] = [{'email': email} for email in event.attendees]
        updated_event = service.events().update(
            calendarId='primary',
            eventId=event_id,
            body=existing
        ).execute()
        return {"id": updated_event['id'], "htmlLink": updated_event['htmlLink']}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/events/{event_id}")
def delete_event(event_id: str):
    """
    Delete (cancel) an event.
    """
    try:
        service = get_calendar_service()
        service.events().delete(calendarId='primary', eventId=event_id).execute()
        return {"status": "deleted"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/events/{event_id}/reschedule")
def reschedule_event(event_id: str, start: str, end: str):
    """
    Reschedule an event to a new time.
    """
    try:
        service = get_calendar_service()
        event = service.events().get(calendarId='primary', eventId=event_id).execute()
        event['start'] = {'dateTime': start, 'timeZone': 'UTC'}
        event['end'] = {'dateTime': end, 'timeZone': 'UTC'}
        updated_event = service.events().update(
            calendarId='primary',
            eventId=event_id,
            body=event
        ).execute()
        return {"id": updated_event['id'], "htmlLink": updated_event['htmlLink']}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))