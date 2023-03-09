import aiohttp
import config
import re
from deep_translator import GoogleTranslator

def translate(text,src=None,dst=None):
    return GoogleTranslator(source=src, target=dst).translate(text)

async def generate(chardef, exdialog, history):
    history_en = translate(history,"ru","en")
    # inp = input("You: ")
    # history += "You: " + inp
    prompt = chardef + exdialog + history_en + "\nTasya:"
    # print(prompt)
    model_data = [50,True,0.5,0.9,1,1.1,0,0,0,1,0,1,True,"You","Tasya","",True,1500,1]
    req_json = {"data":[prompt,] + model_data}
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=600)) as session:
        async with session.post("http://"+config.pygip+":"+config.pygport+"/run/textgen", json=req_json) as resp:
            print("---")
            print((await resp.json())["data"][0][-200:])
            print("---")
            said = re.findall(r'(?:Tasya:)(.*)', (await resp.json())["data"][0])
            # print(said[-1])
            return translate(said[-1],"en","ru")
            # print("\nTasya: " + said[-1] + "\n")
            # history += "\nTasya: " + said[-1] + "\n"
    # print("***")
    # print(history)
    # print("***")
