import asyncio
import os
import sys

from dotenv import load_dotenv

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from llm.google import GoogleLanguageModel
from llm.openai import OpenAILanguageModel
from playwright_helper import PlaywrightHelper
from tools.google_stock_tool import GoogleStockTool
from tools.tool import Tool

load_dotenv()


async def main() -> None:
    company_name = input("> ")
    async with PlaywrightHelper(launch_options={"headless": True}) as playwright_helper:
        # language models
        # openai_llm = OpenAILanguageModel()
        googleai_llm = GoogleLanguageModel()

        googleStockTool: Tool = GoogleStockTool(
            source_params={"company_name_query": company_name},
            playwright=playwright_helper,
            llm=googleai_llm,
        )

        print(f"Pulling stock information for: {company_name}, please wait...")
        result = await googleStockTool.pull_content()
        googleStockTool.pretty_print_stock_data(result)


if __name__ == "__main__":
    asyncio.run(main())
