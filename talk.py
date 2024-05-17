import aiohttp
import config
import re
import logging
from deep_translator import GoogleTranslator, DeeplTranslator

logger = logging.getLogger("talk")

async def translate(text,src=None,dst=None):
    # try to use best, fallback to "just good"
    try:
        return DeeplTranslator(api_key=config.deepl_key,source=src,target=dst).translate(text)
    except:
        logger.warning("DeepL translator failed")
        return GoogleTranslator(source=src,target=dst).translate(text)

def fix_name(text):
    return re.sub(r'Tas.a',"Tasya",text)

def fix_pipes(text):
    return re.sub(r"\|\|", "|", text)

# Direct LLaMA generation
async def generate_old(prompt, history, lock):
    try:
        history_en = fix_name(await translate(history,"ru","en"))
    except:
        logger.error("Translation to english failed")
        return "Иди нахер, животное. Я отдыхаю."

    full_prompt = prompt + history_en + "\n<|start_header_id|>model<|end_header_id|>: "

    req_json = {"prompt":full_prompt, "model": "llama3", "raw": True, "stream": False}
    try:
        async with lock:
            logger.info("Asking Pyg for response")
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=600)) as session:
                async with session.post("http://"+config.ollama_ip+":"+config.ollama_port+"/api/generate", json=req_json) as resp:
                    text = (await resp.json())["response"]
                    logger.info(f"Pyg resp: {text}")
    except:
        logger.error("Pyg error")
        return "Иди нахер, животное. Я отдыхаю."
    try:
        return await translate(text,"en","ru")
    except:
        logger.error("Translation to russian failed")
        return "Иди нахер, животное. Я отдыхаю."

# RAG wrapper
async def generate(prompt, history, lock):
    try:
        history_en = fix_pipes(fix_name(await translate(history,"ru","en")))
    except:
        logger.error("Translation to english failed")
        return "Иди нахер, животное. Я отдыхаю."
    
    req_json = {"history":history_en}
    try:
        async with lock:
            logger.info("Asking Pyg for response")
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=600)) as session:
                async with session.post("http://localhost:8085/text_input", json=req_json) as resp:
                    text = (await resp.json())["text"]
                    logger.info(f"Pyg resp: {text}")
    except:
        logger.error("Pyg error")
        return "Иди нахер, животное. Я отдыхаю."
    try:
        return await translate(text,"en","ru")
    except:
        logger.error("Translation to russian failed")
        return "Иди нахер, животное. Я отдыхаю."
