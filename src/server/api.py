from fastapi import FastAPI
from fastapi.responses import StreamingResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
#from model import vLLM_Engine
from models import gpt_Engine
import json

app= FastAPI()
llm= gpt_Engine() 
#llm= vLLM_Engine()

app.mount("/client", StaticFiles(directory="../client"), name="client")
#app.mount("/images", StaticFiles(directory="/home/abiel/workspace/Flickr30k/flickr30k_images/flickr30k_images"), name="images")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Question(BaseModel):
    text: str


@app.get("/", response_class=HTMLResponse)
async def read_root():
    with open("client/index.html", "r") as f:
        return f.read()
    
@app.post("/generate")
async def generate(question: Question):

    async def event_generator():

        text_buffer = ""
        image_index = 0
        async for token in llm(question.text):

            text_buffer += token
            if "<|IMG|>" in text_buffer:
                image_url = llm.retrieved_images[image_index] #must index [0] if using composite indexer

                yield f"data: {json.dumps({'type': 'image', 'data': image_url})}\n\n"
                image_index += 1
                text_buffer = text_buffer.replace("<|IMG|>", "")

            if len(text_buffer) > 0:

                yield f"data: {json.dumps({'type': 'text', 'data': text_buffer})}\n\n"
                text_buffer = ""

        if text_buffer:

            yield f"data: {json.dumps({'type': 'text', 'data': text_buffer})}\n\n"
            
        yield f"data: {json.dumps({'type': 'terminator', 'data': '[DONE]'})}\n\n"
        llm.retrieved_images= list()
        image_index = 0

    return StreamingResponse(event_generator(), media_type="text/event-stream")