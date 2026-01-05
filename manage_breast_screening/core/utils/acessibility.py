from axe_playwright_python.base import AxeResults
from axe_playwright_python.sync_playwright import Axe

AXE_VIOLATIONS_EXCLUDE_LIST = [
    "region",  # 'Some page content is not contained by landmarks' https://github.com/alphagov/govuk-frontend/issues/1604
    "aria-allowed-attr",  # 'ARIA attribute is not allowed: aria-expanded="false"' https://github.com/alphagov/govuk-frontend/issues/979
    "color-contrast-enhanced",  # Ignore 'Element has insufficient color contrast' for WCAG Level AAA
]


class AxeAdapter(Axe):
    def __init__(self):
        # fmt: off
        self.default_options = {
            "rules": {
                id: {"enabled": False} for id in AXE_VIOLATIONS_EXCLUDE_LIST
            },
            "runOnly": {
                "type": "tag",
                "values": [
                    "best-practice",

                    # WCAG 2.x
                    "wcag2a",
                    "wcag2aa",
                    "wcag2aaa",

                    # WCAG 2.1
                    "wcag21a",
                    "wcag21aa",

                    # WCAG 2.2
                    "wcag22aa"
                ]
            }
        }
        # fmt: on

        super().__init__()

    def run(self, page, context=None, options=None) -> AxeResults:
        return super().run(
            page=page, context=context, options=options or self.default_options
        )
