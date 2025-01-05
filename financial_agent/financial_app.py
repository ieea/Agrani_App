from pydantic_ai import Agent
from pydantic import BaseModel, Field
from dataclasses import dataclass
import pydantic
import requests
import dotenv
import os
from pydantic_ai import Agent, RunContext, ModelRetry
from pydantic_ai.result import RunResult
from typing import Any, Optional, Dict, Union, Annotated
from datetime import date, datetime
import pydantic_ai
from IPython.display import display, Markdown
import logfire
from fastapi import FastAPI, Request
from pydantic import BaseModel
from typing import Optional, List
from fastapi.responses import JSONResponse
from fastapi import HTTPException
from fastapi.responses import FileResponse, Response, StreamingResponse

#logfire.configure()

#dotenv.load_dotenv('/content/drive/MyDrive/Colab Notebooks/.env')
dotenv.load_dotenv()

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
FINANCIAL_MODELING_PREP_API_KEY = os.getenv('FINANCIAL_MODELING_PREP_API_KEY')
GROQ_API_KEY = os.getenv('GROQ_API_KEY')


class ManagerResult(BaseModel): 
    message: str
    

@dataclass
class ManagerDependencies:
    # Use Annotated to provide metadata for pydantic
    income_statement_agent: Annotated[Any, Field(..., arbitrary_types_allowed=True)]
    stock_price_agent: Annotated[Any, Field(..., arbitrary_types_allowed=True)] 
    company_basic_information_agent: Annotated[Any, Field(..., arbitrary_types_allowed=True)]
    symbol: str = Field(description="The symbol of the company")
        
manager_agent = Agent(
#'openai:gpt-4o-mini',
"groq:llama3-groq-70b-8192-tool-use-preview",
result_type=ManagerResult,
deps_type=ManagerDependencies,
system_prompt=("Extract the symbol of the requested company. Determine which agent is best suited to handle the user's request, and transfer the conversation to that agent."),
)

@manager_agent.tool
async def call_income_statement_agent(ctx:RunContext[ManagerDependencies], text: str, deps: ManagerDependencies) -> Dict[str, Any]: # Changed return type to Dict
    """
    Call the income statement agent if the text contains 'income statement'.
    """
    if "income statement" in text:
        
        # result= await ctx.deps.income_statement_agent.run(deps.symbol)
        # return result

      try:
        result = await ctx.deps.income_statement_agent.run(deps.symbol)
        # Generate Markdown from the result
        markdown_output = generate_markdown_income_statement(result.data)
        # Return the Markdown as a message
        return {"message": markdown_output}
      except ValueError as e:
            return {"status": "error", "message": str(e)}
      
    else:
        return {"status": "error", "message": "No agent available for this request."}    

@manager_agent.tool
async def call_stock_price_agent(ctx:RunContext[ManagerDependencies], text: str, deps: ManagerDependencies) -> Dict[str, Any]: # Changed return type to Dict
    """
    Call the stock price agent if the text contains 'stock price'.
    """
    if "stock price" in text:
        # return await ctx.deps.stock_price_agent.run(deps.symbol)
        try:
            result = await ctx.deps.stock_price_agent.run(deps.symbol)
            # Generate Markdown from the result
            markdown_output = generate_markdown_stock_price(result.data)
            # Return the Markdown as a message
            return {"message": markdown_output}
        except ValueError as e:
            return {"status": "error", "message": str(e)}
    else:
         return {"status": "error", "message": "No agent available for this request."}

@manager_agent.tool
async def call_company_basic_information_agent(ctx:RunContext[ManagerDependencies], text: str, deps: ManagerDependencies) -> Dict[str, Any]: # Changed return type to Dict

     """
     Call the company basic information agent if the text contains 'company information'.
     """
     if "company information" in text:
         #return await ctx.deps.company_basic_information_agent(deps.symbol)
        try:
            result = await ctx.deps.company_basic_information_agent.run(deps.symbol)
            # Generate Markdown from the result
            markdown_output = generate_markdown_company_info(result.data)
            # Return the Markdown as a message
            return {"message": markdown_output}
        except ValueError as e:
            return {"status": "error", "message": str(e)}
     else:
         return {"status": "error", "message": "No agent available for this request."}

class StockPriceResult(BaseModel):
    symbol:str = Field(description="The symbol of the company")
    price:float = Field(description="The price of the company")
    volume:float = Field(description="The volume of the company")
    priceAvg50:float = Field(description="The 50 day average price of the company")
    priceAvg200:float = Field(description="The 200 day average price of the company")
    eps:float = Field(description="The EPS of the company")
    pe:float = Field(description="The PE of the company")
    earningsAnnouncement:datetime = Field(description="The earnings announcement of the company")

stock_price_agent = Agent (
"groq:llama3-groq-70b-8192-tool-use-preview",
result_type=StockPriceResult,
system_prompt=("Fetch Hsitorical prices for a given stock symbol, the current,volume, the average price 50d and 200d, EPS, PE and the next earnings, Announcement."),
)

@stock_price_agent.tool_plain
def get_stock_price(symbol:str)->dict:
    """
    Fetch the current stock price for the given symbol, the current volume, the 
    average price 50d and 200d, EPS, PE and the next earnings Announcement.
    """
    url = f"https://financialmodelingprep.com/api/v3/quote-order/{symbol}?apikey={FINANCIAL_MODELING_PREP_API_KEY}"
    response = requests.get(url)
    data = response.json()
    try:
        results = data[0]
        financials = StockPriceResult(**data[0])
        return financials
        
    except (IndexError, KeyError):
        return {"error": f"Could not fetch stock details for symbol: {symbol}"}
    


class CompanyInfoResult(BaseModel): 
    symbol:str =  Field(description="The symbol of the company")
    companyName:str =  Field(description="The name of the company")
    marketCap:float = Field(alias="mktCap", description="The market capitalization of the company")
    industry:str =  Field(description="The industry of the company")
    sector:str =  Field(description="The sector of the company")
    website:str =  Field(description="The website of the company")
    beta:float = Field(description="The beta of the company")
    price:float = Field(description="The price of the company")

company_basic_information_agent = Agent(
"groq:llama3-groq-70b-8192-tool-use-preview",
result_type=CompanyInfoResult,
system_prompt=("Fetch basic financial information for the given company, symbol such as the industry, the sector, the name of the company, and the ,market capitalization."),
)
@company_basic_information_agent.tool_plain
def get_company_info(symbol:str)->dict:
    """
    Fetch the basic financial information for the given company symbol, such as the industry, the sector, the name of the company, and the market capitalization.
    """
    url = f"https://financialmodelingprep.com/api/v3/profile/{symbol}?apikey={FINANCIAL_MODELING_PREP_API_KEY}"
    response = requests.get(url)
    data = response.json()
    
    try:
        results = data[0]
        financials = CompanyInfoResult(**data[0])
        return financials
        
    except (IndexError, KeyError):
        return {"error": f"Could not fetch company information for symbol: {symbol}"}
    

class IncomeStatementResult(BaseModel):
    """
    Fetch the last income statement for the given company symbol, such as revenue, gross profit, net income, EBITDA, EPS.
    """
    date_field: date = Field(alias='date', description="The date of the income statement")
    revenue:float = Field(description="The revenue of the company")
    gross_profit:float = Field(alias='grossProfit', description="The gross profit of the company")
    net_income:float = Field(alias='netIncome', description="The net income of the company")
    ebitda:float = Field(description="The EBITDA of the company")
    eps:float = Field(description="The EPS of the company")
    eps_diluted:float = Field(alias='epsdiluted', description="The EPS diluted of the company")

income_statement_agent = Agent(
"groq:llama3-groq-70b-8192-tool-use-preview",
result_type=IncomeStatementResult,
system_prompt=("Fetch last income statement for the given company symbol, such as revenue, gross profit, net income, EBITDA, EPS. Use the get_income_statement tool to generate the statement"),

)

@income_statement_agent.tool_plain
def get_income_statement(symbol:str)->dict:
    """
    Fetch the last income statement for the given company symbol, such as revenue, gross profit, net income, EBITDA, EPS.
    """
    print("Symbol:", symbol)
    url = f"https://financialmodelingprep.com/api/v3/income-statement/{symbol}?apikey={FINANCIAL_MODELING_PREP_API_KEY}"
    
    response = requests.get(url)
    data = response.json()
    try:
        results = data[0]
        financials = IncomeStatementResult(**data[0])
        return financials

    except (IndexError, KeyError):
        return {"error": f"Could not fetch financials for symbol: {symbol}"}

def print_prompt(prompt: str):
    print("*" * 80)
    print(f"Prompt: {prompt}")
    print("*" * 80)

def generate_markdown_income_statement(income_statement:IncomeStatementResult) -> str:
  return f"""
    ## Income Statement (as of {income_statement.date_field})
    - **Revenue**: ${income_statement.revenue: .2f}
    - **Gross Profit**: ${income_statement.gross_profit: .2f}
    - **Net Income**: ${income_statement.net_income: .2f}
    - **EBITDA**: ${income_statement.ebitda: .2f}
    - **EPS**: {income_statement.eps: .2f}
    - **EPS (Diluted)**: {income_statement.eps_diluted: .2f}
    """ if income_statement else "No income statement was obtained"


def generate_markdown_stock_price(stock_price:StockPriceResult) -> str:
    return f"""
    ## Stock Price Information
    - **Current Price**: ${stock_price.price: .2f}
    - **Volume**: {stock_price.volume: .2f}
    - **50-Day Average Price**: ${stock_price.priceAvg50: .2f}
    - **200-Day Average Price**: ${stock_price.priceAvg200: .2f}
    - **EPS**: {stock_price.eps: .2f}
    - **PE Ratio**: {stock_price.pe: .2f}
    - **Earnings Announcement**: {stock_price.earningsAnnouncement}
    """ if stock_price else "No stock price information was obtained"

def generate_markdown_company_info(company_info:CompanyInfoResult) -> str:
    return f"""
    ## Company Information
    - **Symbol**: {company_info.symbol}
    - **Company Name**: {company_info.companyName}
    - **Market Capitalization**: ${company_info.marketCap: .2f}
    - **Industry**: {company_info.industry}
    - **Sector**: {company_info.sector}
    - **Website**: {company_info.website}
    - **Beta**: {company_info.beta: .2f}
    - **Price**: ${company_info.price: .2f}
    """ if company_info else "No company information was obtained"

app = FastAPI()

class PromptRequest(BaseModel):
    prompt:str



@app.post("/api/prompt")
async def process_prompt(request: Request, prompt_request: PromptRequest):
    prompt = prompt_request.prompt

    deps = ManagerDependencies(
        income_statement_agent=income_statement_agent,
        stock_price_agent=stock_price_agent,
        company_basic_information_agent=company_basic_information_agent
    )

    results = []  # Collect yielded values here
    try:
        async with manager_agent.run_stream(prompt, deps=deps) as result:
            message = ""
            print(result.stream_text())
            async for text in result.stream(debounce_by=0.01):
                message = text.message
                results.append({  # Append each partial result
                    "prompt": prompt,
                    "result": message
                })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing prompt: {str(e)}")

    return results  # Return the collected results
    #return StreamingResponse(stream_messages(), media_type='text/plain')

import uvicorn
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)


# async def main():
#     #print("111111111111111111111111111111111111111111111111111")
#     print(f"Pydantic version {pydantic.__version__}")
#     print(f"Pydantic version {pydantic_ai.__version__}")

    
#     deps = ManagerDependencies(
#         income_statement_agent=income_statement_agent, 
#         stock_price_agent=stock_price_agent, 
#         company_basic_information_agent=company_basic_information_agent
#         )
#     prompt = 'What is the latest stock price, company information and income statement of Apple?'
#     print_prompt(prompt)
#     async with manager_agent.run_stream(prompt,deps=deps) as result:
#         async for text in result.stream():
            
#             print(text)

#     #result = manager_agent.run_sync(prompt, deps=deps)
#     #print(result.data.message)
#     #display(Markdown(result.data.message))

# # To run the async function
# import asyncio
# #asyncio.run(main())

# if __name__ == '__main__':
#     asyncio.run(main())

