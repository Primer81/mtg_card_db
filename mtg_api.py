import itertools
import requests
import pickle
import sys

from collections import OrderedDict
from pathlib import Path
from typing import Iterable

MTG_API_ENDPOINT_CARDS = 'https://api.magicthegathering.io/v1/cards'
MTG_CARDS_PICKLE_PATH = Path('mtg_cards.db')


def main():
    mtg_cards: list = load_all_mtg_cards()
    print(f"Loaded {len(mtg_cards)} cards from MTG API")


def load_all_mtg_cards() -> list:
    mtg_cards: list
    if not MTG_CARDS_PICKLE_PATH.exists():
        mtg_cards = list(get_all_mtg_cards_from_api())
        dump_all_mtg_cards_into_pickle(mtg_cards)
    else:
        mtg_cards = load_all_mtg_cards_from_pickle()
    return mtg_cards


def load_all_mtg_cards_from_pickle() -> list:
    with MTG_CARDS_PICKLE_PATH.open(mode='br') as fp:
        mtg_cards: list = list(pickle.load(fp))
    return mtg_cards


def dump_all_mtg_cards_into_pickle(mtg_cards: iter) -> None:
    with MTG_CARDS_PICKLE_PATH.open(mode='bw') as fp:
        pickle.dump(list(mtg_cards), fp)


def get_all_mtg_cards_from_api() -> iter:
    return itertools.chain.from_iterable(get_all_mtg_card_pages())


def get_all_mtg_card_pages() -> Iterable[iter]:
    page: int = 0  # 787 is roughly the last page
    while True:
        mtg_cards_page_raw: dict = get_raw_mtg_cards_from_page(page)
        if not mtg_cards_page_raw["cards"]:
            break
        page += 1
        mtg_cards_page: iter = mtg_cards_page_raw["cards"]
        yield mtg_cards_page


def get_raw_mtg_cards_from_page(page=0) -> dict:
    url: str = MTG_API_ENDPOINT_CARDS
    params: dict = {"page": page}
    data: dict = {}
    resp = requests.get(url, params=params, json=data)
    print(resp.status_code, resp.url)
    return resp.json()


if __name__ == "__main__":
    sys.exit(main())
