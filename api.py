from fastapi import FastAPI, Request
from pydantic import BaseModel
from indexer import Indexer

app = FastAPI()
indexer = Indexer()
indexer.load_index()

class AskRequest(BaseModel):
    question: str

@app.post("/ask")
async def ask(req: AskRequest):
    answer = indexer.query(req.question)
    return {"answer": str(answer)} 