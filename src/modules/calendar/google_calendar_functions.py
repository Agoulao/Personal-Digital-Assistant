################################################################################################################
# IMPORTANT: Requires 'client_secret.json' from Google Calendar in the resources directory.
# Navigate to Google Cloud Console, create a project, enable Calendar API,
# add the following scope "https://www.googleapis.com/auth/calendar.events" in Google Auth Platform/Data access,
# https://mail.google.com/ is also needed if gmail_automation.py is enabled
# and download the OAuth 2.0 credentials as 'client_secret(...).json'.
# Rename it to 'client_secret.json' and place it in the 'modules/resources' directory.
#################################################################################################################


import functools
import logging
import datetime
import os.path
import json
import time # For performance measurement

# Google API imports
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Date parsing library (no longer used for direct parsing, but for internal datetime objects)
from dateutil import parser
from dateutil.relativedelta import relativedelta
import pytz

from modules.base_functions import BaseAutomationModule # Import the base class
from typing import Dict, Any

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/calendar.events']

# Decorator for safe execution and uniform error handling
def safe_action(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except HttpError as error:
            logging.error(f"Google Calendar API Error in {func.__name__}: {error}", exc_info=True)
            return f"[FAIL] Failed to {func.__name__.replace('_', ' ')}. Google Calendar API error: {error.resp.status} - {error.content.decode()}"
        except ValueError as ve:
            logging.error(f"Data parsing error in {func.__name__}: {ve}", exc_info=True)
            return f"[FAIL] Failed to {func.__name__.replace('_', ' ')}. Invalid input data: {ve}"
        except Exception as e:
            logging.error(f"Error in {func.__name__}: {e}", exc_info=True)
            return f"[FAIL] Failed to {func.__name__.replace('_', ' ')}. An unexpected error occurred: {e}"
    return wrapper

class GoogleCalendarAutomation(BaseAutomationModule):
    """
    Provides automation for Google Calendar via its API.
    Requires Google API setup, authentication, and credentials.
    """

    def __init__(self):
        self.module_dir = os.path.dirname(os.path.abspath(__file__))
        self.resources_dir = os.path.join(self.module_dir, '..', 'resources')
        self.token_path = os.path.join(self.resources_dir, 'token.json')
        self.client_secret_path = os.path.join(self.resources_dir, 'client_secret.json')
        
        self.local_tz = pytz.timezone('Europe/Lisbon') 

        print("DEBUG: Authenticating Google Calendar API...")
        auth_start_time = time.time()
        self.service = self._authenticate_google_calendar()
        auth_end_time = time.time()
        print(f"DEBUG: Google Calendar API authentication took {auth_end_time - auth_start_time:.2f} seconds.")

        if self.service == "AUTHENTICATION_FAILED":
            print("WARNING: Google Calendar API authentication failed. Calendar features will be unavailable.")
            self.is_authenticated = False
        else:
            self.is_authenticated = True
            print("INFO: GoogleCalendarAutomation module initialized and authenticated.")

    def _authenticate_google_calendar(self):
        """
        Handles Google Calendar API authentication using OAuth 2.0.
        It looks for 'token.json' and creates it if not found or expired.
        Requires 'client_secret.json' in the same directory as this module.
        """
        creds = None
        if os.path.exists(self.token_path):
            print("DEBUG: Found existing token.json.")
            creds = Credentials.from_authorized_user_file(self.token_path, SCOPES)
        
        if not creds or not creds.valid:
            print("DEBUG: Credentials not valid or not found. Initiating fresh authentication.")
            if creds and creds.expired and creds.refresh_token:
                print("DEBUG: Refreshing expired token.")
                creds.refresh(Request())
            else:
                try:
                    print("DEBUG: Running local server for OAuth flow.")
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.client_secret_path, SCOPES)
                    creds = flow.run_local_server(port=0)
                except FileNotFoundError:
                    print(f"ERROR: client_secret.json not found at {self.client_secret_path}. Please download it from Google Cloud Console and place it in the same directory as this script.")
                    return "AUTHENTICATION_FAILED"
                except Exception as e:
                    print(f"ERROR: Google Calendar authentication failed: {e}")
                    return "AUTHENTICATION_FAILED"
            # Save the credentials for the next run
            with open(self.token_path, 'w') as token:
                token.write(creds.to_json())
            print("DEBUG: New token.json saved.")
        else:
            print("DEBUG: Credentials are valid.")
        
        if creds:
            try:
                return build('calendar', 'v3', credentials=creds)
            except Exception as e:
                print(f"ERROR: Failed to build Google Calendar service: {e}")
                return "AUTHENTICATION_FAILED"
        return "AUTHENTICATION_FAILED"


    def get_description(self) -> str:
        """
        Returns a brief description of the module's capabilities for the LLM's conversational context.
        """
        return "manage events and appointments in Google Calendar (list, create, and delete events)."

    def get_supported_actions(self) -> Dict[str, Dict[str, Any]]:
        if not self.is_authenticated:
            return {}

        return {
            "list_events": {
                "method_name": "list_calendar_events",
                "description": "Lists upcoming calendar events for a specified time period. The time_period can be a single date (YYYY-MM-DD), a specific datetime (YYYY-MM-DDTHH:MM:SS), or a range (YYYY-MM-DD/YYYY-MM-DD).",
                "example_json": '{"action":"list_events","time_period":"2025-07-01/2025-07-31"}'
            },
            "create_event": {
                "method_name": "create_calendar_event",
                "description": "Creates a new calendar event with a summary, start time, and optional end time and description. Times must be in ISO 8601 format (YYYY-MM-DDTHH:MM:SS for specific times, or INSEE-MM-DD for all-day).",
                "example_json": '{"action":"create_event","summary":"Team Sync","start_time":"2025-07-01T10:00:00","end_time":"2025-07-01T11:00:00","description":"Discuss Q3 goals"}'
            },
            "delete_event": {
                "method_name": "delete_calendar_event",
                "description": "Deletes a calendar event by its summary and optional time period. The summary should be an exact or very close match to an existing event. Time period must be in ISO 8601 format (YYYY-MM-DD or INSEE-MM-DD/YYYY-MM-DD).",
                "example_json": '{"action":"delete_event","summary":"Team Sync","time_period":"2025-07-01"}'
            },
            "delete_events_range": {
                "method_name": "delete_calendar_events_in_range",
                "description": ("Bulk delete events within a time range (YYYY-MM-DD[/YYYY-MM-DD]) with an optional summary filter. If summary is provided, only events whose title contains that text (case-insensitive) are removed."),
                "example_json": '{"action":"delete_events_range","time_period":"2025-10-16/2025-10-23","summary":"meeting"}'
            },
            # Add more calendar actions as needed
        }


    # Adiciona isto algures na classe GoogleCalendarAutomation (por ex. antes de list_calendar_events)
    def _compute_time_window(self, time_period: str | None):
        """
        Converte um descritor de período numa janela [timeMin, timeMax] em ISO UTC.
        - None  => semana corrente (2ª 00:00 -> domingo 23:59:59, hora local)
        - 'YYYY-MM-DD' => esse dia
        - 'YYYY-MM-DDTHH:MM:SS' => janela de 1 minuto a partir desse instante
        - 'YYYY-MM-DD/YYYY-MM-DD' ou com datetimes => intervalo [start, end]
        """
        if time_period is None:
            # Semana corrente (segunda a domingo) em hora local
            now_local = datetime.datetime.now(self.local_tz)
            monday_local = (now_local - datetime.timedelta(days=(now_local.weekday()))).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            sunday_local = monday_local + datetime.timedelta(days=6, hours=23, minutes=59, seconds=59, microseconds=999999)
            time_min = monday_local.astimezone(pytz.utc).isoformat().replace('+00:00', 'Z')
            time_max = sunday_local.astimezone(pytz.utc).isoformat().replace('+00:00', 'Z')
            return time_min, time_max, "this_week"

        if '/' in time_period:
            start_str, end_str = time_period.split('/')
            # tenta datetime completo, senão assume data
            try:
                start_dt_local = self.local_tz.localize(datetime.datetime.fromisoformat(start_str.replace('Z', '')))
            except ValueError:
                start_dt_local = self.local_tz.localize(datetime.datetime.strptime(start_str, '%Y-%m-%d')).replace(
                    hour=0, minute=0, second=0, microsecond=0
                )
            try:
                end_dt_local = self.local_tz.localize(datetime.datetime.fromisoformat(end_str.replace('Z', '')))
            except ValueError:
                end_dt_local = self.local_tz.localize(datetime.datetime.strptime(end_str, '%Y-%m-%d')).replace(
                    hour=23, minute=59, second=59, microsecond=999999
                )
            return (
                start_dt_local.astimezone(pytz.utc).isoformat().replace('+00:00', 'Z'),
                end_dt_local.astimezone(pytz.utc).isoformat().replace('+00:00', 'Z'),
                time_period
            )

        # data única ou datetime único
        if 'T' in time_period:
            dt_local = self.local_tz.localize(datetime.datetime.fromisoformat(time_period.replace('Z', '')))
            time_min = dt_local.astimezone(pytz.utc).isoformat().replace('+00:00', 'Z')
            time_max = (dt_local + datetime.timedelta(minutes=1)).astimezone(pytz.utc).isoformat().replace('+00:00', 'Z')
            return time_min, time_max, time_period
        else:
            date_local = self.local_tz.localize(datetime.datetime.strptime(time_period, '%Y-%m-%d'))
            time_min = date_local.replace(hour=0, minute=0, second=0, microsecond=0).astimezone(pytz.utc).isoformat().replace('+00:00', 'Z')
            time_max = (date_local + datetime.timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0).astimezone(pytz.utc).isoformat().replace('+00:00', 'Z')
            return time_min, time_max, time_period


    @safe_action
    def list_calendar_events(self, time_period: str = "today") -> str:
        """
        Lists events for a specified time period.
        time_period is expected to be in ISO 8601 format (YYYY-MM-DD, INSEE-MM-DDTHH:MM:SS, or INSEE-MM-DD/YYYY-MM-DD).
        """
        if not self.is_authenticated:
            return "Google Calendar API not authenticated."
        
        try:
            time_min_iso, time_max_iso, period_label = self._compute_time_window(time_period)
        except Exception as e:
            raise ValueError(f"Invalid ISO 8601 date/time format for time_period: '{time_period}'. Error: {e}")


        print(f"DEBUG: Calling Google Calendar API to list events (timeMin={time_min_iso}, timeMax={time_max_iso})...")
        api_call_start_time = time.time()
        events_result = self.service.events().list(
            calendarId='primary',
            timeMin=time_min_iso,
            timeMax=time_max_iso, # Will be None if no time_period specified
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        api_call_end_time = time.time()
        print(f"DEBUG: Google Calendar API list events call took {api_call_end_time - api_call_start_time:.2f} seconds.")

        events = events_result.get('items', [])

        if not events:
            return f"No upcoming events found for the period: {time_period}."
        
        output = f"Upcoming events for {time_period}:\n"
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            end = event['end'].get('dateTime', event['end'].get('date'))
            summary = event.get('summary', 'No Title')
            location = event.get('location')
            
            try:
                if 'dateTime' in event['start']:
                    # Specific time event (can cross days)
                    start_dt_utc = datetime.datetime.fromisoformat(start.replace('Z', '+00:00'))
                    start_dt_local = start_dt_utc.astimezone(self.local_tz)
                    
                    end_dt_utc = datetime.datetime.fromisoformat(end.replace('Z', '+00:00'))
                    end_dt_local = end_dt_utc.astimezone(self.local_tz)
                    
                    if start_dt_local.date() == end_dt_local.date():
                        # SAME DAY EVENT: YYYY-MM-DD (Day), HH:MM–HH:MM
                        date_display = start_dt_local.strftime('%Y-%m-%d (%a)')
                        time_display = f"{start_dt_local.strftime('%H:%M')}–{end_dt_local.strftime('%H:%M')}"
                        time_range_display = f"{date_display}, {time_display}"
                    else:
                        # MULTI-DAY EVENT: Start: YYYY-MM-DD (Day), HH:MM | End: YYYY-MM-DD (Day), HH:MM
                        start_str = start_dt_local.strftime('Start: %Y-%m-%d (%a), %H:%M')
                        end_str = end_dt_local.strftime('End: %Y-%m-%d (%a), %H:%M')
                        time_range_display = f"{start_str} | {end_str}"
                    
                else: 
                    # All-day event (date string)
                    start_date_obj = datetime.datetime.fromisoformat(start).date()
                    end_date_obj = datetime.datetime.fromisoformat(end).date() - datetime.timedelta(days=1)
                    
                    if start_date_obj == end_date_obj:
                         # Single-day all-day event: YYYY-MM-DD (Day)
                         time_range_display = f"ALL-DAY: {start_date_obj.strftime('%Y-%m-%d (%a)')}"
                    else:
                        # Multi-day all-day event: ALL-DAY: YYYY-MM-DD to YYYY-MM-DD
                        time_range_display = f"ALL-DAY: {start_date_obj.isoformat()} to {end_date_obj.isoformat()}"
                    
            except Exception as e:
                time_range_display = f"Error formatting time: {e}"
                logging.warning(f"Failed to format event time for display: {e}. Raw: {start} to {end}")
                
            # Combine
            details = [time_range_display]
            if location:
                details.append(f"Location: {location}")

            output += f"- {summary} — {' | '.join(details)}\n"
        # -----------------------------------
        return output

    @safe_action
    def create_calendar_event(self, summary: str, start_time: str, end_time: str = None, description: str = None) -> str:
        """
        Creates a new calendar event.
        start_time and end_time are expected to be in ISO 8601 format (YYYY-MM-DDTHH:MM:SS or INSEE-MM-DD), local time.
        """
        if not self.is_authenticated:
            return "Google Calendar API not authenticated."

        event = {
            'summary': summary,
            'description': description,
        }

        # Determine if it's an all-day event or specific time event based on 'T'
        is_all_day_start = 'T' not in start_time # Check for 'T' to signify time component

        if is_all_day_start:
            # All-day event: LLM provides INSEE-MM-DD (local date)
            start_date_obj = datetime.datetime.strptime(start_time, '%Y-%m-%d').date()
            event['start'] = {'date': start_time} # Google Calendar handles date-only events correctly
            # For all-day events, end date is exclusive, so it's the day *after* the event ends
            if end_time and 'T' not in end_time:
                end_date_obj = datetime.datetime.strptime(end_time, '%Y-%m-%d').date()
                event['end'] = {'date': (end_date_obj + datetime.timedelta(days=1)).isoformat()}
            else:
                event['end'] = {'date': (start_date_obj + datetime.timedelta(days=1)).isoformat()} # Default 1-day event
        else:
            # Specific time event: LLM provides INSEE-MM-DDTHH:MM:SS (local time)
            try:
                start_time_clean = start_time.replace('Z', '') # Remove 'Z' if present
                # Parse as local datetime, then convert to UTC for Google Calendar
                start_dt_local = self.local_tz.localize(datetime.datetime.fromisoformat(start_time_clean))
                event['start'] = {'dateTime': start_dt_local.astimezone(pytz.utc).isoformat().replace('+00:00', 'Z')}
                event['start']['timeZone'] = 'UTC' # Explicitly set timezone to UTC for Google if we're sending UTC datetime

                if end_time:
                    end_time_clean = end_time.replace('Z', '') # Remove 'Z' if present
                    end_dt_local = self.local_tz.localize(datetime.datetime.fromisoformat(end_time_clean))
                    event['end'] = {'dateTime': end_dt_local.astimezone(pytz.utc).isoformat().replace('+00:00', 'Z')}
                    event['end']['timeZone'] = 'UTC'
                else:
                    # If no end_time, assume 1-hour event. Calculate end_time in local, then convert to UTC.
                    end_dt_local = start_dt_local + datetime.timedelta(hours=1)
                    event['end'] = {'dateTime': end_dt_local.astimezone(pytz.utc).isoformat().replace('+00:00', 'Z')}
                    event['end']['timeZone'] = 'UTC'
                    
                start_display = start_dt_local.strftime('%Y-%m-%d (%a), %H:%M')
                end_display = end_dt_local.strftime('%H:%M') # Only time for end is usually sufficient
                    
            except ValueError as e:
                raise ValueError(f"Invalid start_time format for specific time event: {start_time}. Error: {e}")

        print(f"DEBUG: Calling Google Calendar API to create event (summary='{summary}', start_time='{start_time}')...")
        api_call_start_time = time.time()
        event = self.service.events().insert(calendarId='primary', body=event).execute()
        api_call_end_time = time.time()
        print(f"DEBUG: Google Calendar API create event call took {api_call_end_time - api_call_start_time:.2f} seconds.")
        if is_all_day_start:
             if start_display == end_display:
                 time_range_str = f"All-day on {start_display}"
             else:
                 time_range_str = f"All-day from {start_display} to {end_display}"
        else:
             time_range_str = f"{start_display}-{end_display}"


        details = [time_range_str]
        if description:
            # Truncate description for a concise display
            details.append(f"Description: {description[:50]}..." if len(description) > 50 else f"Description: {description}")

        return f"Event '{event.get('summary')}' created successfully. Details:\n- {' | '.join(details)}"

    @safe_action
    def delete_calendar_event(self, summary: str, time_period: str = None) -> str:
        """
        Deletes a calendar event by its summary.
        It will search for events matching the summary within the specified time period.
        If multiple events match, it will delete the first one found.
        time_period is expected to be in ISO 8601 format (YYYY-MM-DD or INSEE-MM-DD/YYYY-MM-DD), local time.
        """
        if not self.is_authenticated:
            return "Google Calendar API not authenticated."

        time_min_iso = None
        time_max_iso = None

        if time_period:
            try:
                time_min_iso, time_max_iso, _ = self._compute_time_window(time_period)
            except Exception as e:
                raise ValueError(f"Invalid time_period: '{time_period}'. Error: {e}")
        else:
            now_local = datetime.datetime.now(self.local_tz)
            time_min_iso = now_local.astimezone(pytz.utc).isoformat().replace('+00:00', 'Z')
            time_max_iso = None  # futuro aberto

        print(f"DEBUG: Calling Google Calendar API to list events for deletion search (timeMin={time_min_iso}, timeMax={time_max_iso})...")
        api_call_start_time = time.time()
        events_result = self.service.events().list(
            calendarId='primary',
            timeMin=time_min_iso,
            timeMax=time_max_iso, # Will be None if no time_period specified
            q=summary, # Query for events matching the summary
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        api_call_end_time = time.time()
        print(f"DEBUG: Google Calendar API list events for deletion search took {api_call_end_time - api_call_start_time:.2f} seconds.")

        events = events_result.get('items', [])

        # Filter events by summary (case-insensitive and partial match for forgiveness)
        matching_events = [
            event for event in events 
            if summary.lower() in event.get('summary', '').lower()
        ]

        if not matching_events:
            return f"No event found with summary matching '{summary}' for the period: {time_period if time_period else 'any upcoming time'}."
        
        if len(matching_events) > 1:
            logging.warning(f"Multiple events found matching '{summary}'. Deleting the first one: '{matching_events[0].get('summary')}'")
            
        event_to_delete = matching_events[0]
        event_id = event_to_delete['id']
        event_summary = event_to_delete['summary']
        
        try:
            start = event_to_delete['start'].get('dateTime', event_to_delete['start'].get('date'))
            end = event_to_delete['end'].get('dateTime', event_to_delete['end'].get('date'))
            
            if 'dateTime' in event_to_delete['start']:
                # Specific time event
                start_dt_utc = datetime.datetime.fromisoformat(start.replace('Z', '+00:00'))
                start_dt_local = start_dt_utc.astimezone(self.local_tz)
                end_dt_utc = datetime.datetime.fromisoformat(end.replace('Z', '+00:00'))
                end_dt_local = end_dt_utc.astimezone(self.local_tz)
                
                # Check for cross-day event
                if start_dt_local.date() == end_dt_local.date():
                    date_display = start_dt_local.strftime('%Y-%m-%d (%a)')
                    time_display = f"{start_dt_local.strftime('%H:%M')}–{end_dt_local.strftime('%H:%M')}"
                    time_range_display = f"{date_display}, {time_display}"
                else:
                    start_str = start_dt_local.strftime('%Y-%m-%d (%a), %H:%M')
                    end_str = end_dt_local.strftime('%Y-%m-%d (%a), %H:%M')
                    time_range_display = f"{start_str} to {end_str}"
            else:
                # All-day event
                start_date_obj = datetime.datetime.fromisoformat(start).date()
                end_date_obj = datetime.datetime.fromisoformat(end).date() - datetime.timedelta(days=1)
                
                if start_date_obj == end_date_obj:
                     time_range_display = f"All-day {start_date_obj.strftime('%Y-%m-%d (%a)')}"
                else:
                    time_range_display = f"All-day from {start_date_obj.isoformat()} to {end_date_obj.isoformat()}"
        
        except Exception as e:
            time_range_display = f"Time parsing error: {e}"
        
        # Details now only contains the time range
        details = [time_range_display]

        print(f"DEBUG: Calling Google Calendar API to delete event (ID={event_id}, Summary='{event_summary}')...")
        api_call_start_time = time.time()
        self.service.events().delete(calendarId='primary', eventId=event_id).execute()
        api_call_end_time = time.time()
        print(f"DEBUG: Google Calendar API delete event call took {api_call_end_time - api_call_start_time:.2f} seconds.")
        output = f"Deleted 1 event matching '{summary}' in {time_period if time_period else 'any upcoming time'}:\n"
        output += f"- {event_summary} — {' | '.join(details)}"
        return output


    @safe_action
    def delete_calendar_events_in_range(self, time_period: str, summary: str = None) -> str:
        """
        Bulk delete of events inside a time range.
        - time_period: 'YYYY-MM-DD/YYYY-MM-DD' (ou com datetimes)
        - summary (opcional): substring case-insensitive a procurar no título
        """
        if not self.is_authenticated:
            return "Google Calendar API not authenticated."

        if not time_period or '/' not in time_period:
            raise ValueError("time_period must be a date or datetime range: 'YYYY-MM-DD/YYYY-MM-DD'.")

        try:
            time_min_iso, time_max_iso, _ = self._compute_time_window(time_period)
        except Exception as e:
            raise ValueError(f"Invalid time_period: '{time_period}'. Error: {e}")

        print(f"DEBUG: Listing events for bulk delete (timeMin={time_min_iso}, timeMax={time_max_iso})...")
        events_result = self.service.events().list(
            calendarId='primary',
            timeMin=time_min_iso,
            timeMax=time_max_iso,
            singleEvents=True,
            orderBy='startTime',
            q=summary if summary else None
        ).execute()

        items = events_result.get('items', [])
        if summary:
            items = [ev for ev in items if summary.lower() in ev.get('summary', '').lower()]

        if not items:
            return f"No events found to delete for period '{time_period}'" + (f" matching '{summary}'." if summary else ".")

        deleted_details = []
        deleted = 0
        for ev in items:
            try:
                # --- PREPARE DISPLAY BEFORE DELETION (Location REMOVED) ---
                start = ev['start'].get('dateTime', ev['start'].get('date'))
                end = ev['end'].get('dateTime', ev['end'].get('date'))
                event_summary = ev.get('summary', 'No Title')
                
                if 'dateTime' in ev['start']:
                    start_dt_utc = datetime.datetime.fromisoformat(start.replace('Z', '+00:00'))
                    start_dt_local = start_dt_utc.astimezone(self.local_tz)
                    end_dt_utc = datetime.datetime.fromisoformat(end.replace('Z', '+00:00'))
                    end_dt_local = end_dt_utc.astimezone(self.local_tz)
                    
                    # Check for cross-day event
                    if start_dt_local.date() == end_dt_local.date():
                        date_display = start_dt_local.strftime('%Y-%m-%d (%a)')
                        time_display = f"{start_dt_local.strftime('%H:%M')}–{end_dt_local.strftime('%H:%M')}"
                        time_range_display = f"{date_display}, {time_display}"
                    else:
                        start_str = start_dt_local.strftime('%Y-%m-%d (%a), %H:%M')
                        end_str = end_dt_local.strftime('%Y-%m-%d (%a), %H:%M')
                        time_range_display = f"{start_str} to {end_str}"
                else:
                    # All-day event
                    start_date_obj = datetime.datetime.fromisoformat(start).date()
                    end_date_obj = datetime.datetime.fromisoformat(end).date() - datetime.timedelta(days=1)
                    
                    if start_date_obj == end_date_obj:
                         time_range_display = f"All-day {start_date_obj.strftime('%Y-%m-%d (%a)')}"
                    else:
                        time_range_display = f"All-day from {start_date_obj.isoformat()} to {end_date_obj.isoformat()}"
                
                details = [time_range_display] # Only contains the time range
                # ---------------------------------------

                self.service.events().delete(calendarId='primary', eventId=ev['id']).execute()
                deleted_details.append(f"- {event_summary} — {''.join(details)}")
                deleted += 1
            except Exception as e:
                logging.error(f"Failed to delete event '{ev.get('summary','')}' ({ev.get('id')}): {e}")

        filter_str = f" matching '{summary}'" if summary else ""
        output = f"Deleted {deleted} event(s) for period {time_period}{filter_str}:\n"
        output += '\n'.join(deleted_details)
        return output
