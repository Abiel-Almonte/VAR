import re
from openai import AsyncOpenAI
import os
import sys
import logging
from os.path import join, dirname
from dotenv import load_dotenv
from typing import AsyncGenerator

sys.path.insert(0, '../util')
from util import IMG_PROMPT, get_img_url, functions

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

dotenv_path = join(dirname(__file__), "..", "..", '.env')
load_dotenv(dotenv_path)

class gpt_Engine:
    def __init__(self):
        self.async_client = AsyncOpenAI(api_key=os.getenv('OPENAI_KEY'))
        self.retrieved_images = []

    async def __call__(self, question: str) -> AsyncGenerator[str, None]:
        prompt = IMG_PROMPT.format(question=question)

        try:
            stream = await self.async_client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            stream=True,
        )
            
        except Exception as e:
            logger.error(f"Error creating chat completion: {e}")
            yield f"An error occurred: {str(e)}"
            return

        buffer = ""
        image_request_pattern = re.compile(r'<IMAGE_REQUEST>(.*?)</IMAGE_REQUEST>')

        async for chunk in stream:
            try:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    buffer += content
                    
                    while True:
                        match = image_request_pattern.search(buffer)
                        if not match:
                            break
                        
                        before_tag = buffer[:match.start()]
                        image_description = match.group(1)
                        after_tag = buffer[match.end():]
                        
                        if before_tag:
                            yield before_tag
                        
                        try:
                            logger.debug(f"Image generated query: {image_description}")
                            image_url = get_img_url(image_description)
                            self.retrieved_images.append(image_url)
                            yield "<|IMG|>"

                        except Exception as e:
                            logger.error(f"Error processing image request: {e}")
                        
                        buffer = after_tag
                    
                    sentences = buffer.split('. ')
                    if len(sentences) > 1:
                        yield '. '.join(sentences[:-1]) + '. '
                        buffer = sentences[-1]

            except Exception as e:
                logger.error(f"Error processing stream chunk: {e}")
                yield f"An error occurred while processing the response: {str(e)}"

        if buffer:
            yield buffer

        logger.info("Stream processing completed")
