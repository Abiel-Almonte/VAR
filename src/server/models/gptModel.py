from openai import AsyncOpenAI
from collections import deque
import os, sys
from os.path import join, dirname
from dotenv import load_dotenv

sys.path.insert(0, '../util')
from util import IMG_PROMPT, get_img_url

dotenv_path = join(dirname(__file__), "..", "..", '.env')
load_dotenv(dotenv_path)

class gpt_Engine():
    def __init__(self, window_size:int= 200):

        self.client= AsyncOpenAI(api_key= os.getenv('OPENAI_KEY'))
        self.retrieved_images= list()
        self.tokens_window= deque(maxlen= window_size)

    async def __call__(
        self,
        question: str,
    ):
        prompt= IMG_PROMPT.format(question= question)

        stream= await self.client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[{"role": "user", "content": IMG_PROMPT.format(question= prompt)}],
            stream=True,
        )

        async for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                text=chunk.choices[0].delta.content

                if "IMG" in text:
                    self.retrieved_images.append(get_img_url(''.join(list(self.tokens_window))))
                    yield "<|IMG|>"

                else:
                    self.tokens_window.extend(text)
                    yield text