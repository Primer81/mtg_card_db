import scryfall_prices
import sheets_range
import scryfall_api
import google_api
import datetime
import pprint
import util
import sys

from google.oauth2.credentials import Credentials
from googleapiclient.errors import HttpError
from sheets_range import SheetsRange
from collections import OrderedDict
from card_info import CardInfo, FoilType
from typing import Any, Optional

# The ID of the target spreadsheet.
GOOGLE_SPREADSHEET_ID = '12BXt6lJo7ianQ6jLRUhm4_LWBtvs7sOqH9fncMbAw8k'
GOOGLE_SPREADSHEET_SHEET_NAME = 'Collection'

GOOGLE_SPREADSHEET_HEADER_COL_OFFSET = 0
GOOGLE_SPREADSHEET_HEADER_COL_START = util.number_to_column_letter(GOOGLE_SPREADSHEET_HEADER_COL_OFFSET)

GOOGLE_SPREADSHEET_RANGE_HEADER = f'{GOOGLE_SPREADSHEET_SHEET_NAME}!{GOOGLE_SPREADSHEET_HEADER_COL_START}1:1'
GOOGLE_SPREADSHEET_RANGE_CARD_INFO = f'{GOOGLE_SPREADSHEET_SHEET_NAME}' \
                                     f'!{GOOGLE_SPREADSHEET_HEADER_COL_START}:E'
GOOGLE_SPREADSHEET_SELECT_COLUMN_DATA = f'{GOOGLE_SPREADSHEET_SHEET_NAME}!' + '{0}2:{0}'

# Format string to select a range as follows:
# {0} - Column Start
# {1} - Column End
# {2} - Row Start
# {3} - Row End
GOOGLE_SPREADSHEET_SELECT_RANGE_DATA = f'{GOOGLE_SPREADSHEET_SHEET_NAME}!' + '{0}{2}:{1}{3}'


def main():
    update_spreadsheet_with_scryfall_price_data()


def update_spreadsheet_with_scryfall_price_data() -> None:
    creds: Credentials = google_api.obtain_google_api_credentials()
    try:
        sheet = google_api.obtain_google_api_service(creds)
        header: list[tuple[str, str]] = obtain_header_from_sheet(sheet)
        price_column: str = get_prices_column_from_header(header)
        print(clear_column_in_sheet(sheet, price_column))
        raw_card_info: list[list[str]] = obtain_raw_card_info_from_sheet(sheet)
        all_card_info: list[Optional[CardInfo]] = process_raw_card_info(raw_card_info)
        prices: list[str] = find_price_for_all_card_info(all_card_info)
        price_range: SheetsRange = SheetsRange(price_column, price_column, 2, 100_000)
        update_range_with_data(sheet, price_range, [prices], major_dimension="COLUMNS")
    except HttpError as err:
        print(err)


def find_price_for_all_card_info(all_card_info: list[Optional[CardInfo]]) -> list[str]:
    prices: list[str] = []
    for card_info in all_card_info:
        price: str = ''
        if card_info:
            try:
                price = scryfall_prices.find_price_for_card_info(card_info)
            except KeyError:
                print(f"Failed to lookup the price of card: {card_info}")
                pass
        prices.append(price)
    return prices


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


def obtain_header_from_sheet(sheet: Any) -> list[tuple[str, str]]:
    result = sheet.values().get(spreadsheetId=GOOGLE_SPREADSHEET_ID,
                                range=GOOGLE_SPREADSHEET_RANGE_HEADER).execute()
    header = result.get('values', [])[0]
    return [(value, util.number_to_column_letter(col))
            for col, value in
            enumerate(header, start=GOOGLE_SPREADSHEET_HEADER_COL_OFFSET)]


def obtain_raw_card_info_from_sheet(sheet: Any) -> list[list[str]]:
    result = sheet.values().get(spreadsheetId=GOOGLE_SPREADSHEET_ID,
                                range=GOOGLE_SPREADSHEET_RANGE_CARD_INFO).execute()
    return result.get('values', [])


def process_raw_card_info(raw_card_info: list[list[str]]) -> list[Optional[CardInfo]]:
    header = raw_card_info[0]
    all_card_info: list[Optional[CardInfo]] = []
    for row in raw_card_info[1:]:
        card_info: Optional[CardInfo] = None
        card_name: Optional[str] = None
        collector_number: Optional[str] = None
        set_id: Optional[str] = None
        language: Optional[str] = None
        foil_type: Optional[FoilType] = None
        for attr, value in zip(header, row):
            if attr == "Card Name":
                card_name = value
            elif attr == "Collector Number":
                collector_number = value
            elif attr == "Set":
                set_id = value
            elif attr == "Language":
                language = value
            elif attr == "Foil":
                foil_type = get_foil_type_from_str(value)
            else:
                # Ignore this attribute
                pass
        if card_name and collector_number and set_id and language and foil_type:
            card_info = CardInfo(card_name, set_id, collector_number, language, foil_type)
        all_card_info.append(card_info)
    return all_card_info


def get_foil_type_from_str(foil_type: str) -> FoilType:
    result: FoilType
    if foil_type == "None":
        result = FoilType.NONE
    elif foil_type == "Traditional":
        result = FoilType.TRADITIONAL
    elif foil_type == "Surge":
        result = FoilType.SURGE
    else:
        raise ValueError(f"Could not match foil type string to type: {foil_type}")
    return result


def get_prices_column_from_header(header: list[tuple[str, str]]) -> str:
    price_column: Optional[str] = None
    for head in header:
        if head[0] == "Prices":
            price_column = head[1]
    if price_column is None:
        raise ValueError("Failed to find the 'Prices' column in spreadsheet")
    return price_column


def clear_column_in_sheet(sheet: Any, column: str) -> Any:
    sheet_range: str = GOOGLE_SPREADSHEET_SELECT_COLUMN_DATA.format(column)
    result = sheet.values().clear(spreadsheetId=GOOGLE_SPREADSHEET_ID,
                                  range=sheet_range).execute()
    return result


if __name__ == "__main__":
    sys.exit(main())
