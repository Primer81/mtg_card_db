import google_api
import mtg_api
import sys

from google.oauth2.credentials import Credentials
from googleapiclient.errors import HttpError
from typing import Any


def update_all_columns_with_mtg_data(sheet: Any, mtg_cards: list, columns: list[tuple[str, str]]) -> None:
    for attr, column in columns:
        col_data: list = []
        for idx, card in enumerate(mtg_cards):
            value = card.get(attr)
            if type(value) is list:
                value = value[0]
            col_data.append(value)
        print(google_api.update_column_with_data(sheet, column, col_data))


def main():
    mtg_cards: list = mtg_api.load_all_mtg_cards()
    creds: Credentials = google_api.obtain_google_api_credentials()
    try:
        sheet = google_api.obtain_google_api_service(creds)
        print(google_api.clear_all_data_in_sheet(sheet))
        print(google_api.update_refresh_timestamp(sheet))
        columns: list[tuple[str, str]] = google_api.obtain_target_columns(sheet)
        print(columns)
        update_all_columns_with_mtg_data(sheet, mtg_cards, columns)
    except HttpError as err:
        print(err)


if __name__ == '__main__':
    sys.exit(main())
