import asyncio
import os
import sys

from dotenv import load_dotenv

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from llm.google import GoogleLanguageModel
from llm.openai import OpenAILanguageModel
from playwright_helper import PlaywrightHelper
from sources.datasource import Datasource
from sources.google_stock_datasource import GoogleStockDatasource

load_dotenv()


async def main() -> None:
    company_name = input("> ")
    async with PlaywrightHelper(launch_options={"headless": True}) as playwright_helper:
        # language models
        # openai_llm = OpenAILanguageModel()
        googleai_llm = GoogleLanguageModel()

        googleStockDatasource: Datasource = GoogleStockDatasource(
            source_params={"company_name_query": company_name},
            playwright=playwright_helper,
            llm=googleai_llm,
        )

        print(f"Pulling stock information for: {company_name}, please wait...")
        result = await googleStockDatasource.pull_content()
        googleStockDatasource.pretty_print_stock_data(result)


if __name__ == "__main__":
    asyncio.run(main())
