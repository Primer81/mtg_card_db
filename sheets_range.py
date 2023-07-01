import util

from typing import NamedTuple


class SheetsRange(NamedTuple):
    col_start: str
    col_end: str
    row_start: int
    row_end: int


def range_from_integers(col_start: int, col_end: int, row_start: int, row_end: int) -> SheetsRange:
    col_start: str = util.number_to_column_letter(col_start)
    col_end: str = util.number_to_column_letter(col_end)
    return SheetsRange(col_start, col_end, row_start, row_end)