import itertools
import requests
import pickle
import sys

from pathlib import Path

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


def get_all_mtg_card_pages() -> iter:
    page: int = 0  # 787 is roughly the last page
    while True:
        mtg_cards_page_raw: dict = get_raw_mtg_cards_from_page(page)
        if not mtg_cards_page_raw["cards"]:
            break
        page += 1
        mtg_cards_page: iter = process_mtg_cards(mtg_cards_page_raw)
        yield mtg_cards_page


def get_raw_mtg_cards_from_page(page=0) -> dict:
    url: str = MTG_API_ENDPOINT_CARDS
    params: dict = {"page": page}
    data: dict = {}
    resp = requests.get(url, params=params, json=data)
    print(resp.status_code, resp.url)
    return resp.json()


def process_mtg_cards(cards: dict) -> iter:
    cards_by_name: dict[str, dict] = dict()
    attributes_to_keep: set[str] = {"id", "name", "manaCost", "types", "rarity", "setName", "cmc", "imageUrl"}
    cards_seq: list = list(cards["cards"])

    for card in cards_seq:
        card_name = card["name"]
        if card_name not in cards_by_name or card.get("imageUrl") is not None:
            cards_by_name[card_name] = card

    def __filter_card_attrs(attr: tuple):
        return attr[0] in attributes_to_keep

    def __map_mtg_cards(card_: dict):
        return dict(filter(__filter_card_attrs, card_.items()))

    return map(__map_mtg_cards, cards_by_name.values())


if __name__ == "__main__":
    sys.exit(main())
