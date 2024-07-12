import requests, json
kwargs= json.load(open('customSearchArgs.json'))

def get_img_url(text: str):

    kwargs['params']['q']=text

    return requests.get(**kwargs).json()['items'][0]['link']
