import pprint
import json
import sys

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from pathlib import Path
from typing import Any, Optional


# If modifying these scopes, delete the file token.json file.
GOOGLE_API_SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
GOOGLE_API_TOKEN = Path('token.json')
GOOGLE_API_CREDENTIALS = Path('credentials.json')


def main():
    creds: Credentials = obtain_google_api_credentials()
    pprint.pprint(json.loads(creds.to_json()))


def obtain_google_api_service(creds: Credentials) -> Any:
    service = build('sheets', 'v4', credentials=creds)
    return service.spreadsheets()


def obtain_google_api_credentials() -> Credentials:
    creds: Optional[Credentials] = None
    # The file GOOGLE_API_TOKEN stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if GOOGLE_API_TOKEN.exists():
        creds = Credentials.from_authorized_user_file(str(GOOGLE_API_TOKEN), GOOGLE_API_SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                str(GOOGLE_API_CREDENTIALS), GOOGLE_API_SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds


if __name__ == "__main__":
    sys.exit(main())