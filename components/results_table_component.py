"""Results table reused by any screen that shows tabular data.

Example target: https://the-internet.herokuapp.com/tables (table "#table1").
A component is used from a page or a task exactly like a page: it returns
data and never decides what to do with it.
"""

from __future__ import annotations

from core.base_page import BasePage
from core.engines.base_engine import BaseEngine


class ResultsTableComponent(BasePage):
    TBL_RESULTS = "#table1"
    # Locator templates use str.format placeholders, filled in by the methods.
    TBL_RESULTS_ROW = "{table} tbody tr:nth-of-type({row_number})"
    TBL_RESULTS_CELL = "{table} tbody tr:nth-of-type({row_number}) td:nth-of-type({column_number})"

    def __init__(self, engine: BaseEngine, base_url: str, table_locator: str = TBL_RESULTS) -> None:
        super().__init__(engine, base_url)
        self._table_locator = table_locator

    def wait_until_loaded(self) -> None:
        self._wait_for(self._table_locator)

    def has_results(self) -> bool:
        return self._is_visible(self.TBL_RESULTS_ROW.format(table=self._table_locator, row_number=1))

    def get_cell_text(self, row_number: int, column_number: int) -> str:
        """Row and column numbers start at 1, like the table the user sees."""
        locator = self.TBL_RESULTS_CELL.format(
            table=self._table_locator, row_number=row_number, column_number=column_number
        )
        return self._get_text(locator)
