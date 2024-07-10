from vllm import AsyncLLMEngine, AsyncEngineArgs, SamplingParams
from transformers import AutoTokenizer
from collections import deque
import uuid, asyncio
from vectordb import CLIPCompositeIndexer
from consts import*


class vLLM_Engine():
    def __init__(self, window_size:int= 50):

        engine_args= AsyncEngineArgs(
            MODEL,
            dtype=DTYPE,
            max_model_len=MAX_LEN,
            gpu_memory_utilization=GPU_UTIL,
            disable_log_requests= True,
        )

        self.tokens= deque(maxlen=window_size)
        self.similarity_threshold = 0.8
        self.special_token_count=0
        self.vectorDB= CLIPCompositeIndexer()
        self.images= []
        self.tokenizer= AutoTokenizer.from_pretrained(MODEL)
        self.llm= AsyncLLMEngine.from_engine_args(engine_args)
    
    async def inference(
        self,
        prompt: str,
        _uuid: str,
        temperature: float= 0.0,
        max_tokens:int= 2048,
        stream: bool= False
    ):
        
        response_generator= self.llm.generate(
            prompt,
            SamplingParams(
                temperature=temperature,
                max_tokens=max_tokens,
                skip_special_tokens=False,
                spaces_between_special_tokens=False,
            ),
            _uuid
        )

        output= await self.output_response(response_generator, stream)

        self.special_token_count=0
        async for text in output:
            self.post_process(text)

    async def output_response(
        self,
        response_generator,
        stream: bool,
    ):
        if stream: return self.stream_output(response_generator)

        else: return await self.static_output(response_generator) 
                
    async def stream_output(self, response_generator):
        counter= 0
        async for request_output in response_generator:
            output= request_output.outputs[0]
            text= output.text[counter:]
            yield text
            counter+= len(text)

    async def static_output(self, response_generator):
        async for request_output in response_generator: pass
        if request_output.finished:
            response= request_output.outputs[0].text
            return response
    
    def post_process(self, text:str):
        encoded_input= self.tokenizer(text, add_special_tokens=False).input_ids

        if 32768 in encoded_input: #special token for images <|IMG|>

            if self.special_token_count< 5: 

                self.insert_image(
                    self.tokenizer.decode(list(self.tokens), skip_special_tokens=True))
                self.special_token_count+= 1

        else: 
            print(text, end='')
            self.tokens.extend(encoded_input)
        
    def insert_image(self, text:str):
        print("\n===================\n IMAGE_HERE \n")
        self.images.append(self.vectorDB.search(text))
        print(f"Caption: {self.images[-1][0]['caption']}\n===================\n")
        
    def __call__(
        self,
        question: str,
    ):
        prompt= IMG_PROMPT.format(question= question)
        asyncio.run(self.inference(prompt, str(uuid.uuid4()), stream=True))
        

## TEST
if __name__ == '__main__':
    engine= vLLM_Engine()
    while 1:
        _in = input('Enter prompt: \n')
        if _in != 'end':
            engine(_in)
        else: break