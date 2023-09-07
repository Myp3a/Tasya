import aiohttp
import config
import re
from deep_translator import GoogleTranslator, DeeplTranslator

async def translate(text,src=None,dst=None):
    # try to use best, fallback to "just good"
    try:
        return DeeplTranslator(api_key=config.deepl_key,source=src,target=dst).translate(text)
    except:
        return GoogleTranslator(source=src,target=dst).translate(text)

def fix_name(text):
    return re.sub(r'Tas.a',"Tasya",text)

async def generate(prompt, history, lock):
    try:
        history_en = fix_name(await translate(history,"ru","en"))
    except:
        print("translation to eng error")
        return "Иди нахер, животное. Я отдыхаю."

    full_prompt = prompt + history_en + "\n<|model|>:"

    req_json = {"prompt":full_prompt, "max_context_length":2048, "max_length":150, "quiet": True}
    try:
        async with lock:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=600)) as session:
                async with session.post("http://"+config.pygip+":"+config.pygport+"/api/v1/generate", json=req_json) as resp:
                    text = fix_name((await resp.json())['results'][0]['text'])
                    text = text.split("<|user|>")[0]
                    text = text.replace("<|model|>:","")
    except:
        print("pyg err")
        return "Иди нахер, животное. Я отдыхаю."
    try:
        return await translate(text,"en","ru")
    except:
        print("translation from eng error")
        return "Иди нахер, животное. Я отдыхаю."
        
    
