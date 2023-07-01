from requests import Response
from pathlib import Path


def number_to_column_letter(num: int) -> str:
    return chr(num + 65)


def format_response(response: Response) -> tuple:
    return response.status_code, response.url


def try_remove_file(path: Path) -> bool:
    did_remove: bool = False
    try:
        path.unlink()
        did_remove = True
    except PermissionError as err:
        print(err)
    return did_remove
