import sheets_range
import google_api
import datetime
import mtg_api
import util
import sys

from google.oauth2.credentials import Credentials
from googleapiclient.errors import HttpError
from sheets_range import SheetsRange
from collections import OrderedDict
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

# Format string to select a range as follows:
# {0} - Column Start
# {1} - Column End
# {2} - Row Start
# {3} - Row End
GOOGLE_SPREADSHEET_SELECT_RANGE_DATA = f'{GOOGLE_SPREADSHEET_SHEET_NAME}!' + '{0}{2}:{1}{3}'


def main():
    update_spreadsheet_with_mtg_data()


def update_spreadsheet_with_mtg_data() -> None:
    mtg_cards: list = mtg_api.load_all_mtg_cards()
    mtg_cards: list = process_mtg_cards(mtg_cards)
    creds: Credentials = google_api.obtain_google_api_credentials()
    try:
        sheet = google_api.obtain_google_api_service(creds)
        print(clear_all_data_in_sheet(sheet))
        print(update_refresh_timestamp(sheet))
        columns: list[tuple[str, str]] = obtain_target_columns(sheet)
        print(columns)
        update_all_ranges_with_mtg_data(sheet, mtg_cards, columns)
    except HttpError as err:
        print(err)


def process_mtg_cards(cards: list) -> list:
    cards_by_name: OrderedDict[str, dict] = OrderedDict()

    def __sort_by_name(card_: dict) -> str:
        return card_["name"]
    cards_sorted: list = sorted(cards, key=__sort_by_name)

    for card in cards_sorted:
        card_name = card["name"]
        if card_name not in cards_by_name or card.get("imageUrl") is not None:
            cards_by_name[card_name] = card

    def __map_mtg_cards(card_: dict):
        return dict(card_.items())
    return list(map(__map_mtg_cards, cards_by_name.values()))


def update_all_ranges_with_mtg_data(
        sheet: Any, mtg_cards: list, columns: list[tuple[str, str]]) -> None:
    rows_chunk_count: int = 100_000
    row_start: int = 2
    target_range = sheets_range.range_from_integers(1, 8, row_start, row_start + rows_chunk_count)
    populating: bool = True
    while populating:
        populating = update_one_range_with_mtg_data(sheet, mtg_cards, columns, target_range)
        target_range = SheetsRange(
            target_range.col_start,
            target_range.col_end,
            target_range.row_start + rows_chunk_count,
            target_range.row_end + rows_chunk_count
        )


def update_one_range_with_mtg_data(
        sheet: Any, mtg_cards: list, columns: list[tuple[str, str]], target_range: SheetsRange) -> bool:
    populating: bool = False
    cols: list[list[str]] = []
    for attr, _ in columns:
        col: list[str] = []
        for card in mtg_cards[target_range.row_start:target_range.row_end]:
            populating = True
            value: str = get_attribute_from_card(card, attr)
            col.append(value)
        cols.append(col)
    if populating:
        print(update_range_with_data(sheet, target_range, cols, major_dimension="COLUMNS"))
    return populating


def get_attribute_from_card(card: dict, attr: str) -> str:
    value = card.get(attr)
    if type(value) is list:
        value: str = value[0]
    return value


def update_range_with_data(
        sheet: Any, range_: SheetsRange, data: list[list[str]], major_dimension: str = "ROWS") -> Any:
    column_range = GOOGLE_SPREADSHEET_SELECT_RANGE_DATA.format(
        range_.col_start, range_.col_end, range_.row_start, range_.row_end)
    result = sheet.values().update(spreadsheetId=GOOGLE_SPREADSHEET_ID,
                                   range=column_range,
                                   valueInputOption='RAW',
                                   body=dict(
                                       majorDimension=major_dimension,
                                       values=data
                                   )).execute()
    return result


# def update_all_columns_with_mtg_data(sheet: Any, mtg_cards: list, columns: list[tuple[str, str]]) -> None:
#     for attr, column in columns:
#         col_data: list = []
#         for idx, card in enumerate(mtg_cards):
#             value = card.get(attr)
#             if type(value) is list:
#                 value = value[0]
#             col_data.append(value)
#         print(update_column_with_data(sheet, column, col_data))
#
#
# def update_column_with_data(sheet: Any, column: str, data: list[str]) -> Any:
#     column_range = GOOGLE_SPREADSHEET_SELECT_COLUMN_DATA.format(column)
#     result = sheet.values().update(spreadsheetId=GOOGLE_SPREADSHEET_ID,
#                                    range=column_range,
#                                    valueInputOption='RAW',
#                                    body=dict(
#                                        majorDimension='COLUMNS',
#                                        values=[data]
#                                    )).execute()
#     return result


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
