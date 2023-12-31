from typing import Any, Dict, Optional, TypedDict, cast

from playwright.async_api import Page
from prettytable import PrettyTable

from llm.llm import LanguageModel
from playwright_helper import PlaywrightHelper
from util.html import clean_html
from util.json import json_to_dict

from .datasource import Datasource, DatasourceOptions


class GoogleDatasourceOptions(TypedDict, total=False):
    company_name_query: str
    company_name_resolved: Optional[str]
    eval_company_from_link_prompt: Optional[str]


class GoogleSearchResult(TypedDict, total=False):
    title: str
    link: str


class GoogleDatasourcePromptHelpers(TypedDict, total=False):
    get_stock_prompt: str
    confused_phrase_prompt: str
    eval_company_from_link_prompt: str


class GoogleStockDatasource(Datasource):
    def __init__(self, **opts: DatasourceOptions):
        llm: Optional[LanguageModel] = opts.get("llm")
        if llm == None:
            raise Exception(f"Missing llm")
        self.llm = llm

        datasource_opts: Optional[DatasourceOptions] = opts.get("source_params")
        if datasource_opts == None:
            raise Exception(f"Missing options on {self.name} data source")
        self.datasource_options: GoogleDatasourceOptions = cast(
            GoogleDatasourceOptions, datasource_opts
        )

        playwright: Optional[PlaywrightHelper] = opts.get("playwright")
        if playwright == None:
            raise Exception(f"Missing PlaywrightHelper instance")
        self.playwright: PlaywrightHelper = playwright

    async def pull_content(self) -> str | Dict[str, Any]:
        resolved_name = await self.resolve_company_name_from_input(
            self.datasource_options["company_name_query"]
        )
        resolved_name = resolved_name.strip()
        print(f"Loading recent stock price for {resolved_name}...")
        self.datasource_options["company_name_resolved"] = resolved_name or "N/A"

        company_query = f"{resolved_name} stock financial data market summary"
        company_query_prepped = company_query.replace(" ", "+")
        page = await self.playwright.get_stealth_page()
        await page.goto(
            f"https://www.google.com/search?hl=en&source=hp&biw=&bih=&q={company_query_prepped}"
        )

        await page.wait_for_load_state("networkidle")
        html_pricing_info = ""
        try:
            html_pricing_info = await self.get_price_info(page)
        except Exception as e:
            print(e)
            return "Unable to get financials"

        if self.llm is None:
            raise Exception("LLM is missing")

        prompts = self.get_prompts({"get_stock_prompt": html_pricing_info})
        result = self.llm.get_response_sync(prompts["get_stock_prompt"])
        if result is None:
            raise Exception("LLM returned no result")

        parsedJsonResult = json_to_dict(result)
        if parsedJsonResult is None:
            raise Exception("Invalid JSON parsed")

        company = ""
        if (
            "company_name_resolved" in self.datasource_options
            and self.datasource_options["company_name_resolved"] is not None
        ):
            company = self.datasource_options["company_name_resolved"]
        elif self.datasource_options["company_name_query"] is not None:
            company = self.datasource_options["company_name_query"]

        parsedJsonResult.update({"company": company})
        return parsedJsonResult  # type: ignore[no-any-return]

    async def resolve_company_name_from_input(self, input: str) -> str:
        prompts = self.get_prompts(
            {
                "confused_phrase_prompt": input,
            }
        )

        if self.llm is None:
            raise Exception("LLM is missing")

        # attempt to resolve company name via LLM
        result = self.llm.get_response_sync(prompts["confused_phrase_prompt"])
        if result is None:
            raise Exception("LLM returned no result")
        return cast(str, result)

    async def get_price_info(self, page: Page) -> str:
        price_div = await page.query_selector('div[data-attrid="Price"]')
        if not price_div:
            await self.playwright.take_screenshot(page, "debug_img/init_result.png")
            raise Exception("Unable to locate price")

        await self.playwright.take_screenshot(page, "debug_img/google.png")
        html = await price_div.inner_html()
        return clean_html(html)  # type: ignore[no-any-return]

    def pretty_print_stock_data(self, data: Dict[str, Any]) -> None:
        table = PrettyTable()
        table.field_names = ["Attribute", "Value"]
        table.align["Attribute"] = "l"
        table.align["Value"] = "r"

        for key, value in data.items():
            if isinstance(value, float):
                formatted_value = f"{value:.2f}"
            else:
                formatted_value = str(value)
            table.add_row([key.capitalize(), formatted_value])

        print(table)

    def get_prompts(self, prompt_helpers: Dict[str, Any]) -> Dict[str, str]:
        google_stock_prompts = cast(GoogleDatasourcePromptHelpers, prompt_helpers)
        if "get_stock_prompt" in google_stock_prompts:
            get_google_stock_prompt = (
                "You are a helpful HTML text parsing assistant. I have provided a snippet of HTML code I want you to parse."
                "Please return a JSON object with keys price, currency amt_change and pct_change\n\n"
                f"{google_stock_prompts['get_stock_prompt']}\n\n"
                "The response should only be valid and parseable JSON. It should contain the JSON and nothing else. Do not include the response in markdown, only valid Javascript JSON."
                "The reponse should succeed parsing when calling JSON.parse(results) where results is what you return to me."
            )
            return {
                "get_stock_prompt": get_google_stock_prompt,
            }

        if (
            "confused_phrase_prompt" in google_stock_prompts
            and "eval_company_from_link_prompt" in google_stock_prompts
        ):
            attempt_company_correction_prompt = (
                "You are a helpful business man who knows all the companies in the world. I have provided a vague or mispelled phrase or word and I Want you to tell me what company I'm thinking of."
                "Please return me the name of the company\n\n:"
                f"{google_stock_prompts['eval_company_from_link_prompt']}"
                f"{google_stock_prompts['confused_phrase_prompt']}\n\n"
                "The response should return only the company name and nothing else."
            )
            return {
                "confused_phrase_prompt": attempt_company_correction_prompt,
            }

        if "confused_phrase_prompt" in google_stock_prompts:
            attempt_company_correction_prompt = (
                "You are a helpful business man who knows all the companies in the world. I have provided a vague or mispelled phrase or word and I Want you to tell me what company I'm thinking of."
                "Please return me the name of the company\n\n:"
                f"{google_stock_prompts['confused_phrase_prompt']}\n\n"
                "The response should return only the company name and nothing else."
            )
            return {
                "confused_phrase_prompt": attempt_company_correction_prompt,
            }

        raise Exception("No prompt found")

    async def get_first_search_result(self, page: Page) -> Optional[GoogleSearchResult]:
        await page.wait_for_selector("h3")
        first_result = await page.query_selector("div#search div > div > div")
        if first_result:
            link_element = await first_result.query_selector("a")
            if link_element:
                title_element = await link_element.query_selector("h3")
                if title_element:
                    link = await link_element.get_attribute("href") or ""
                    title = await title_element.inner_text() or ""
                    return {"link": link, "title": title}
                else:
                    print("Title element not found")
                    return None
            else:
                print("Link element not found")
                return None
        else:
            print("No search results found")
            return None

    def name(self) -> str:
        return "Google Stock"
