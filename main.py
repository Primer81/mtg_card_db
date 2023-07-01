import scryfall_to_google_api
import mtg_to_google_api
import sys


def main():
    mtg_to_google_api.main()
    scryfall_to_google_api.main()


if __name__ == '__main__':
    sys.exit(main())
