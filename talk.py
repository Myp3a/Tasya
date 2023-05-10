import aiohttp
import config
import re
from deep_translator import DeeplTranslator

async def translate(text,src=None,dst=None):
    async with aiohttp.ClientSession() as sess:
        async with sess.post("https://api-free.deepl.com/v2/translate", data={"target_lang":dst,"source_lang":src,"text":text}, headers={"Authorization": f"DeepL-Auth-Key {config.deepl_key}"}) as resp:
            return (await resp.json())["translations"][0]["text"]
    return DeeplTranslator(api_key=config.deepl_key, source=src, target=dst).translate(text)

def fix_name(text):
    return re.sub(r'Tas.a',"Tasya",text)

async def generate(chardef, exdialog, history):
    history_en = fix_name(await translate(history,"ru","en"))

    prompt = chardef + exdialog + history_en + "\nTasya:"

    req_json = {"prompt":prompt, 'early_stopping': True}
    print(prompt)
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=600)) as session:
            async with session.post("http://"+config.pygip+":"+config.pygport+"/api/v1/generate", json=req_json) as resp:
                text = fix_name((await resp.json())['results'][0]['text'])
                return await translate(text,"en","ru")
    except:
        return "Иди нахер, животное. Я отдыхаю."