import itertools
import requests
import pickle
import json
import util
import sys

from pathlib import Path
from typing import Optional
from requests import Response

SCRYFALL_API_ENDPOINT_CARD_NAMES = 'https://api.scryfall.com/catalog/card-names'
SCRYFALL_API_ENDPOINT_BULK_DATA = 'https://api.scryfall.com/bulk-data'
SCRYFALL_ALL_CARDS_BULK_DATA_PATH = Path('scryfall-all-cards.json')
SCRYFALL_ALL_CARDS_PICKLE_PATH = Path('scryfall_cards.db')

SCRYFALL_CARD_ATTR_NAME = "name"
SCRYFALL_CARD_ATTR_IMAGE_URIS = "image_uris"


def main():
    scryfall_cards: list = load_all_scryfall_cards()
    example_card: dict = scryfall_cards[0]
    print(f"Loaded {len(scryfall_cards)} cards from Scryfall API")
    print(f"Link to image for '{example_card[SCRYFALL_CARD_ATTR_NAME]}': "
          f"{find_normal_image_uri_in_card(example_card)}")


def find_normal_image_uri_in_card(card: dict):
    image_uris = card.get(SCRYFALL_CARD_ATTR_IMAGE_URIS)
    normal_image_uri: Optional[str] = None
    if image_uris:
        normal_image_uri = image_uris.get("normal")
    if image_uris and not normal_image_uri:
        normal_image_uri = image_uris[0]
    return normal_image_uri


def load_all_scryfall_cards() -> list:
    scryfall_cards: list
    if not SCRYFALL_ALL_CARDS_PICKLE_PATH.exists():
        scryfall_cards = get_scryfall_cards_from_api()
        dump_all_scryfall_cards_into_pickle(scryfall_cards)
        util.try_remove_file(SCRYFALL_ALL_CARDS_BULK_DATA_PATH)
    else:
        scryfall_cards = load_scryfall_cards_from_pickle()
    return scryfall_cards


def dump_all_scryfall_cards_into_pickle(scryfall_cards: list) -> None:
    with SCRYFALL_ALL_CARDS_PICKLE_PATH.open(mode='bw') as fp:
        pickle.dump(scryfall_cards, fp)


def load_scryfall_cards_from_pickle() -> list:
    with SCRYFALL_ALL_CARDS_PICKLE_PATH.open(mode='br') as fp:
        scryfall_cards: list = list(pickle.load(fp))
    return scryfall_cards


def get_scryfall_cards_from_api() -> list:
    bulk_data_info: dict = get_bulk_data_info()
    bulk_data_info_all_data: dict = find_bulk_all_card_data(bulk_data_info)
    print(util.format_response(download_bulk_data(bulk_data_info_all_data)))
    scryfall_cards: list = load_scryfall_cards_from_bulk_data()
    return scryfall_cards


def load_scryfall_cards_from_bulk_data() -> list:
    with SCRYFALL_ALL_CARDS_BULK_DATA_PATH.open(mode='br') as fp:
        all_cards_data = json.load(fp)
    return all_cards_data


def download_bulk_data(bulk_data_info_item: dict) -> Optional[Response]:
    with SCRYFALL_ALL_CARDS_BULK_DATA_PATH.open(mode='bw') as fp:
        response = requests.get(bulk_data_info_item["download_uri"])
        fp.write(response.content)
    return response


def find_bulk_all_card_data(bulk_data_info: dict) -> Optional[dict]:
    bulk_data_info_all_data: Optional[dict] = None
    target_type_name = "all_cards"
    bulk_data_array = bulk_data_info["data"]
    for bulk_data in bulk_data_array:
        if bulk_data["type"] == target_type_name:
            bulk_data_info_all_data = bulk_data
    return bulk_data_info_all_data


def get_bulk_data_info() -> dict:
    url: str = SCRYFALL_API_ENDPOINT_BULK_DATA
    params: dict = {}
    data: dict = {}
    resp = requests.get(url, params=params, json=data)
    print(resp.status_code, resp.url)
    return resp.json()


if __name__ == "__main__":
    sys.exit(main())
