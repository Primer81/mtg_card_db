import requests
import sys

from card_info import CardInfo, FoilType

# Format string to select a range as follows:
# {0} - Set ID (LTR, etc.)
# {1} - Collector Number (225, 235, etc.)
# {2} - Language (EN, RU, etc.)
SCRYFALL_API_ENDPOINT_CARD_SEARCH = 'https://api.scryfall.com/cards/search?include_extras=true&' \
                                    'include_multilingual=true&include_variations=true&unique=prints&' \
                                    'q=e%3A{0}+cn%3A{1}+lang%3A{2}'


def main():
    example_card_info: CardInfo = CardInfo("dummy name", "LTR", "225", "EN", FoilType.SURGE)
    print(find_price_for_card_info(example_card_info))


def find_price_for_card_info(card_info: CardInfo):
    results = search_for_card(card_info)
    cards: list = get_cards_from_search_results(results)
    first_card: dict = cards[0]
    prices: dict = get_prices_from_card(first_card)
    price: str
    if card_info.foil_type == FoilType.NONE:
        price = prices["usd"]
    else:
        price = prices["usd_foil"]
    return price


def search_for_card(card_info: CardInfo) -> dict:
    url: str = SCRYFALL_API_ENDPOINT_CARD_SEARCH.format(
        card_info.set_id, card_info.collector_number, card_info.language)
    params: dict = {}
    data: dict = {}
    resp = requests.get(url, params=params, json=data)
    print(resp.status_code, resp.url)
    return resp.json()


def get_cards_from_search_results(results: dict) -> list:
    print(results)
    return results["data"]


def get_prices_from_card(card: dict) -> dict:
    return card["prices"]


if __name__ == "__main__":
    sys.exit(main())
