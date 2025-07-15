import json

from axe_playwright_python.base import AxeResults
from django.conf import settings
from playwright.sync_api import Page

AXE_VIOLATIONS_EXCLUDE_LIST = [
    "region",  # 'Some page content is not contained by landmarks' https://github.com/alphagov/govuk-frontend/issues/1604
    "aria-allowed-attr",  # 'ARIA attribute is not allowed: aria-expanded="false"' https://github.com/alphagov/govuk-frontend/issues/979
]


class AxeAdapter:
    def __init__(
        self,
        page: Page,
        script_path=settings.BASE_DIR.parent
        / "node_modules"
        / "axe-core"
        / "axe.min.js",
        options=None,
    ):
        self.script_path = script_path
        self.options = options or {
            "rules": {id: {"enabled": False} for id in AXE_VIOLATIONS_EXCLUDE_LIST}
        }
        self.page = page
        self._install(page)

    def _install(self, page: Page):
        """
        Add the axe script to a playwright Page.
        The script will be re-executed any time the page or it's frames are navigated.
        """
        page.add_init_script(path=self.script_path)

    def run(self) -> AxeResults:
        """
        Run axe on the whole document
        """
        options = json.dumps(self.options)
        response = self.page.evaluate(rf"axe.run({options})")
        return AxeResults(response)
