import requests, json, os
from dotenv import load_dotenv
from os.path import join, dirname, abspath

dotenv_path = join(dirname(__file__), '..', '..', '.env')
load_dotenv(dotenv_path)

json_path = join(dirname(abspath(__file__)), 'customSearchArgs.json')

kwargs= json.load(open(json_path))
kwargs['params']['key']= os.getenv('GOOGLE_KEY')
kwargs['params']['cx']= os.getenv('ENGINE_ID')

def get_img_url(text: str):

    kwargs['params']['q']=text

    return requests.get(**kwargs).json()['items'][0]['link']
