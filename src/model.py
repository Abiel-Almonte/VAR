from vllm import AsyncLLMEngine, AsyncEngineArgs, SamplingParams
from transformers import AutoTokenizer
from vectordb import CLIPCompositeIndexer
from collections import deque
from consts import*
import uuid


class vLLM_Engine():
    def __init__(self, window_size:int= 50):

        engine_args= AsyncEngineArgs(
            MODEL,
            dtype=DTYPE,
            max_model_len=MAX_LEN,
            gpu_memory_utilization=GPU_UTIL,
            disable_log_requests= True,
        )

        self.tokens_window= deque(maxlen=window_size)
        self.vectorDB= CLIPCompositeIndexer()
        self.tokenizer= AutoTokenizer.from_pretrained(MODEL)
        self.llm= AsyncLLMEngine.from_engine_args(engine_args)
        self.img_count= 0

        self.retrieved_images= list()

    async def __call__(
        self,
        question: str,
    ):
        prompt= IMG_PROMPT.format(question= question)
        response_generator= self.llm.generate(
            prompt,
            SamplingParams(
                temperature=TEMP,
                max_tokens=MAX_TOKENS,
                skip_special_tokens=False,
                spaces_between_special_tokens=False,
            ),
            str(uuid.uuid4())
        )

        counter= 0
        async for request_output in response_generator:
            output= request_output.outputs[0]
            text= output.text[counter:]
            counter+= len(text)

            encoded_input= self.tokenizer(text, add_special_tokens=False).input_ids

            if IMG_TOKEN in encoded_input: #<|IMG|>

                decoded_query= self.tokenizer.decode(
                    list(self.tokens_window),
                    skip_special_tokens=True)
                
                self.retrieved_images.append(self.vectorDB.search(decoded_query))
                yield "<|IMG|>"

            else:
                self.tokens_window.extend(encoded_input)
                yield text