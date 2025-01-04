from pydantic_ai import Agent
from pydantic import BaseModel, Field
from dataclasses import dataclass
import pydantic
import pydantic_ai
import requests
import dotenv
import os
from pydantic_ai import Agent, RunContext, ModelRetry
from pydantic_ai.result import RunResult
from typing import Any, Optional, Dict, Union, Annotated


dotenv.load_dotenv()
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
FINANCIAL_MODELING_PREP_API_KEY = os.getenv('FINANCIAL_MODELING_PREP_API_KEY')

#OPENAI_API_KEY="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"
GROQ_API_KEY="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"
FINANCIAL_MODELING_PREP_API_KEY="Fx5IHlJfFKrNlJaXZYZgCiNAXOoAIijv"

class ManagerResult(BaseModel): 
#    status: str
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
        
        return await ctx.deps.income_statement_agent.run(deps.symbol)
      
    else:
        return {"status": "error", "message": "No agent available for this request."}    

@manager_agent.tool
async def call_stock_price_agent(ctx:RunContext[ManagerDependencies], text: str, deps: ManagerDependencies) -> Dict[str, Any]: # Changed return type to Dict
    """
    Call the stock price agent if the text contains 'stock price'.
    """
    if "stock price" in text:
         return await ctx.deps.stock_price_agent.run(deps.symbol)
    else:
         return {"status": "error", "message": "No agent available for this request."}

@manager_agent.tool
async def call_company_basic_information_agent(ctx:RunContext[ManagerDependencies], text: str, deps: ManagerDependencies) -> Dict[str, Any]: # Changed return type to Dict

     """
     Call the company basic information agent if the text contains 'company information'.
     """
     if "company information" in text:
         return await ctx.deps.company_basic_information_agent(deps.symbol)
     else:
         return {"status": "error", "message": "No agent available for this request."}

class StockPriceResult(BaseModel):
    symbol: str
    price: float
    volume: float
    priceAvg50: float
    priceAvg200: float
    eps: float
    pe: float
    earningsAnnouncement: str

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
        price = data[0]['price']
        volume = data[0]['volume']
        priceAvg50 = data[0]['priceAvg50']
        priceAvg200 = data[0]['priceAvg200']
        eps = data[0]['eps']
        pe = data[0]['pe']
        earningsAnnouncement = data[0]['earningsAnnouncement']
        return {"symbol": symbol.upper(), "price": price,                   
         "volume":volume,"priceAvg50":priceAvg50,"priceAvg200":priceAvg200, "EPS":eps, "PE":pe, 
         "earningsAnnouncement":earningsAnnouncement }
    except (IndexError, KeyError):
        return {"error": f"Could not fetch price for symbol: {symbol}"}


class CompanyInfoResult(BaseModel): 
    name: str 
    sector: str 
    industry: str 
    summary: str

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
    results = data[0]
    try:
        symbol = results["symbol"],
        companyName = results["companyName"],
        marketCap = results["mktCap"],
        industry = results["industry"],
        sector = results["sector"],
        website = results["website"],
        beta = results["beta"],
        price = results["price"],
        return { "symbol": symbol, "companyName": companyName, "marketCap": marketCap, "industry": industry, "sector": sector, "website": website, "beta": beta, "price": price }
    except (IndexError, KeyError):
        return {"error": f"Could not fetch information for symbol: {symbol}"}
    

class IncomeStatementResult(BaseModel):
    date: str
    revenue: float
    gross_profit: float
    net_income: float
    ebitda: float
    EPS: float
    EPS_diluted: float

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
    print("URL", url)
    response = requests.get(url)
    data = response.json()
    results = data[0]
    try:
        date= results["date"],
        revenue= results["revenue"],
        gross_profit= results["grossProfit"],
        net_income= results["netIncome"],
        ebitda= results["ebitda"],
        EPS=results["eps"],
        EPS_diluted=results["epsdiluted"]
        return { "date": date, "revenue": revenue, "gross_profit": gross_profit, "net_income": net_income, "ebitda": ebitda, "EPS": EPS, "EPS_diluted": EPS_diluted }
    except (IndexError, KeyError):
        return {"error": f"Could not fetch information for symbol: {symbol}"}

def print_prompt(prompt: str):
    print("*" * 80)
    print(f"Prompt: {prompt}")
    print("*" * 80)



def main():
    print("111111111111111111111111111111111111111111111111111")
    print(f"Pydantic version {pydantic.__version__}")
    print(f"Pydantic version {pydantic_ai.__version__}")

    
    deps = ManagerDependencies(
        income_statement_agent=income_statement_agent, 
        stock_price_agent=stock_price_agent, 
        company_basic_information_agent=company_basic_information_agent
        )
    prompt = 'What is the stock price of Amazon?'
    print_prompt(prompt)
    result = manager_agent.run_sync(prompt, deps=deps)
    print(result.data.message)

if __name__ == '__main__':
    main()