import datetime
import util

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from typing import Any, Optional

from pathlib import Path

# If modifying these scopes, delete the file token.json file.
GOOGLE_API_SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
GOOGLE_API_TOKEN = Path('token.json')
GOOGLE_API_CREDENTIALS = Path('credentials.json')

# The ID of the target spreadsheet.
GOOGLE_SPREADSHEET_ID = '1c9XOUGjgSvjcJ_dOG1nCdsLlAP5YFavsFhzEPJIhaKI'
GOOGLE_SPREADSHEET_SHEET_NAME = 'Cards Raw API'

GOOGLE_SPREADSHEET_HEADER_COL_OFFSET = 1
GOOGLE_SPREADSHEET_HEADER_COL_START = util.number_to_column_letter(GOOGLE_SPREADSHEET_HEADER_COL_OFFSET)

GOOGLE_SPREADSHEET_RANGE_HEADER = f'{GOOGLE_SPREADSHEET_SHEET_NAME}!{GOOGLE_SPREADSHEET_HEADER_COL_START}1:1'
GOOGLE_SPREADSHEET_RANGE_ALL_DATA = f'{GOOGLE_SPREADSHEET_SHEET_NAME}!A2:Z'
GOOGLE_SPREADSHEET_CELL_TIMESTAMP = f'{GOOGLE_SPREADSHEET_SHEET_NAME}!A2'
GOOGLE_SPREADSHEET_SELECT_COLUMN_DATA = f'{GOOGLE_SPREADSHEET_SHEET_NAME}!' + '{0}2:{0}'


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


def obtain_google_api_service(creds: Credentials) -> Any:
    service = build('sheets', 'v4', credentials=creds)
    return service.spreadsheets()


def obtain_target_columns(sheet: Any) -> list[tuple[str, str]]:
    result = sheet.values().get(spreadsheetId=GOOGLE_SPREADSHEET_ID,
                                range=GOOGLE_SPREADSHEET_RANGE_HEADER).execute()
    header = result.get('values', [])[0]
    return [(value, util.number_to_column_letter(col))
            for col, value in
            enumerate(header, start=GOOGLE_SPREADSHEET_HEADER_COL_OFFSET)]


def clear_all_data_in_sheet(sheet: Any) -> Any:
    result = sheet.values().clear(spreadsheetId=GOOGLE_SPREADSHEET_ID,
                                  range=GOOGLE_SPREADSHEET_RANGE_ALL_DATA).execute()
    return result


def update_refresh_timestamp(sheet: Any) -> Any:
    result = sheet.values().update(spreadsheetId=GOOGLE_SPREADSHEET_ID,
                                   range=GOOGLE_SPREADSHEET_CELL_TIMESTAMP,
                                   valueInputOption='RAW',
                                   body=dict(
                                       majorDimension='ROWS',
                                       values=[[str(datetime.datetime.now())]]
                                   )).execute()
    return result


def update_column_with_data(sheet: Any, column: str, data: list[str]) -> Any:
    column_range = GOOGLE_SPREADSHEET_SELECT_COLUMN_DATA.format(column)
    result = sheet.values().update(spreadsheetId=GOOGLE_SPREADSHEET_ID,
                                   range=column_range,
                                   valueInputOption='RAW',
                                   body=dict(
                                       majorDimension='COLUMNS',
                                       values=[data]
                                   )).execute()
    return result
