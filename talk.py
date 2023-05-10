import aiohttp
import config
import re
from deep_translator import DeeplTranslator

def translate(text,src=None,dst=None):
    return DeeplTranslator(api_key=config.deepl_key, source=src, target=dst).translate(text)

def fix_name(text):
    return re.sub(r'Tas.a',"Tasya",text)

async def generate(chardef, exdialog, history):
    history_en = fix_name(translate(history,"ru","en"))

    prompt = chardef + exdialog + history_en + "\nTasya:"

    req_json = {"prompt":prompt, 'early_stopping': True}
    print(prompt)
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=600)) as session:
        async with session.post("http://"+config.pygip+":"+config.pygport+"/api/v1/generate", json=req_json) as resp:
            text = fix_name((await resp.json())['results'][0]['text'])
            return translate(text,"en","ru")