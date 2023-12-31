# DirtyRAG

A smol RAG-based framework for working with large language models.

## Motivation

As LLM-based applications scale, especially ones that leverage RAG-based architectures, having more granular control is important. This control should be able to support complex conditional reasoning, hybrid search, agents and more.

## Goals

The goal is to have a minimal LLM RAG framework with support for common RAG-based workflows.

First-class support for popular vector databases to pull embeddings for semantic search (FAISS, ChromaDB, Postgres w/ pgvector) will be imperative to improve relevancy.

Additionally, this tool will have support for building custom agents and tools that can combine with large language models to build complex analysis tools (i.e hybrid search). This will involve defining how iterations are done, chains and conditional reasoning workflows.

# Examples

_Simple RAG based stock lookup using Google GenAI with a custom stock tool_

```python
# DirtyRAG LLM helpers
from llm.google import GoogleLanguageModel
from llm.openai import OpenAILanguageModel

# First-class web scraping tools
from playwright_helper import PlaywrightHelper

# Support for custom tooling for RAG context aggregation
from sources.datasource import Datasource
from sources.google_stock_datasource import GoogleStockDatasource

# Feed in user input
company_name = "billionaire car guy who owns twitter"

async with PlaywrightHelper(launch_options={"headless": True}) as playwright_helper:
    # Choose preferred language model
    # openai_llm = OpenAILanguageModel()
    googleai_llm = GoogleLanguageModel()

    stock_lookup_parameters = {"company_name_query": company_name}
    googleStockDatasource: Datasource = GoogleStockDatasource(
        source_params=stock_lookup_parameters,
        playwright=playwright_helper,
        llm=googleai_llm,
    )

    print(f"Pulling stock information for: {company_name}, please wait...")
    result = await googleStockDatasource.pull_content()
    googleStockDatasource.pretty_print_stock_data(result)
```

_Output_

```
Pulling stock information for: billionaire car guy who owns twitter, please wait...
Loading recent stock price for Tesla...
+------------+--------+
| Attribute  |  Value |
+------------+--------+
| Price      | 239.20 |
| Currency   |    USD |
| Amt_change | -10.03 |
| Pct_change |  4.02% |
| Company    |  Tesla |
+------------+--------+
```
