from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
import json
from agent import FinancialBOT
from fastapi.middleware.cors import CORSMiddleware

fb = FinancialBOT()

app = FastAPI()

origins = [
    "http://localhost",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Cquery(BaseModel):
    name: str
  

@app.post("/run")
async def run_query(q: Cquery):
    return fb.execute_query(q.name)


def execute_query(q):
    #s = '{"q.name" : "Gaurav"}'
    #return json.loads(s)
    return {"Query": q.name,"Name" :"Gaurav"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=3500,
                    workers=4, reload=True)
    



