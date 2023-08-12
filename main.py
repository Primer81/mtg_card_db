import prices.scryfall_prices_to_google_api
import database.scryfall_to_google_api
import database.mtg_to_google_api
import sys


def main():
    database.mtg_to_google_api.main()
    database.scryfall_to_google_api.main()
    prices.scryfall_prices_to_google_api.main()


if __name__ == '__main__':
    sys.exit(main())
