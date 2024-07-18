import aiohttp
import aiohttp.client_exceptions
import config
import re
import logging
from deep_translator import GoogleTranslator, DeeplTranslator, exceptions

logger = logging.getLogger("talk")


async def translate(text, src=None, dst=None):
    # try to use best, fallback to "just good"
    try:
        return DeeplTranslator(
            api_key=config.deepl_key, source=src, target=dst
        ).translate(text)
    except exceptions.BaseError:
        logger.warning("DeepL translator failed")
        return GoogleTranslator(source=src, target=dst).translate(text)


def fix_name(text):
    return re.sub(r"Tas.a", "Tasya", text)


def fix_pipes(text):
    return re.sub(r"\|\|", "|", text)


# RAG wrapper
async def generate(prompt, history, lock):
    req_json = {"history": history, "translate": "ru"}
    try:
        async with lock:
            logger.info("Asking Pyg for response")
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=600)
            ) as session:
                async with session.post(
                    "http://localhost:8085/text_input", json=req_json
                ) as resp:
                    text = (await resp.json())["text"]
                    logger.info(f"Pyg resp: {text}")
    except aiohttp.client_exceptions.ServerTimeoutError:
        logger.error("Pyg error")
        return "Иди нахер, животное. Я отдыхаю."
    return text
