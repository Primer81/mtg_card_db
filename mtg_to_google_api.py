import google_api
import datetime
import mtg_api
import util
import sys

from google.oauth2.credentials import Credentials
from googleapiclient.errors import HttpError
from typing import Any

# The ID of the target spreadsheet.
GOOGLE_SPREADSHEET_ID = '1c9XOUGjgSvjcJ_dOG1nCdsLlAP5YFavsFhzEPJIhaKI'
GOOGLE_SPREADSHEET_SHEET_NAME = 'Cards - MTG API'

GOOGLE_SPREADSHEET_HEADER_COL_OFFSET = 1
GOOGLE_SPREADSHEET_HEADER_COL_START = util.number_to_column_letter(GOOGLE_SPREADSHEET_HEADER_COL_OFFSET)

GOOGLE_SPREADSHEET_RANGE_HEADER = f'{GOOGLE_SPREADSHEET_SHEET_NAME}!{GOOGLE_SPREADSHEET_HEADER_COL_START}1:1'
GOOGLE_SPREADSHEET_RANGE_ALL_DATA = f'{GOOGLE_SPREADSHEET_SHEET_NAME}!A2:Z'
GOOGLE_SPREADSHEET_CELL_TIMESTAMP = f'{GOOGLE_SPREADSHEET_SHEET_NAME}!A2'
GOOGLE_SPREADSHEET_SELECT_COLUMN_DATA = f'{GOOGLE_SPREADSHEET_SHEET_NAME}!' + '{0}2:{0}'


def main():
    update_spreadsheet_with_mtg_data()


def update_spreadsheet_with_mtg_data() -> None:
    mtg_cards: list = mtg_api.load_all_mtg_cards()
    creds: Credentials = google_api.obtain_google_api_credentials()
    try:
        sheet = google_api.obtain_google_api_service(creds)
        print(clear_all_data_in_sheet(sheet))
        print(update_refresh_timestamp(sheet))
        columns: list[tuple[str, str]] = obtain_target_columns(sheet)
        print(columns)
        update_all_columns_with_mtg_data(sheet, mtg_cards, columns)
    except HttpError as err:
        print(err)


def update_all_columns_with_mtg_data(sheet: Any, mtg_cards: list, columns: list[tuple[str, str]]) -> None:
    for attr, column in columns:
        col_data: list = []
        for idx, card in enumerate(mtg_cards):
            value = card.get(attr)
            if type(value) is list:
                value = value[0]
            col_data.append(value)
        print(update_column_with_data(sheet, column, col_data))


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


def update_refresh_timestamp(sheet: Any) -> Any:
    result = sheet.values().update(spreadsheetId=GOOGLE_SPREADSHEET_ID,
                                   range=GOOGLE_SPREADSHEET_CELL_TIMESTAMP,
                                   valueInputOption='RAW',
                                   body=dict(
                                       majorDimension='ROWS',
                                       values=[[str(datetime.datetime.now())]]
                                   )).execute()
    return result


def clear_all_data_in_sheet(sheet: Any) -> Any:
    result = sheet.values().clear(spreadsheetId=GOOGLE_SPREADSHEET_ID,
                                  range=GOOGLE_SPREADSHEET_RANGE_ALL_DATA).execute()
    return result


def obtain_target_columns(sheet: Any) -> list[tuple[str, str]]:
    result = sheet.values().get(spreadsheetId=GOOGLE_SPREADSHEET_ID,
                                range=GOOGLE_SPREADSHEET_RANGE_HEADER).execute()
    header = result.get('values', [])[0]
    return [(value, util.number_to_column_letter(col))
            for col, value in
            enumerate(header, start=GOOGLE_SPREADSHEET_HEADER_COL_OFFSET)]


if __name__ == "__main__":
    sys.exit(main())
