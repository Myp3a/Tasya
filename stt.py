import aiohttp
import config
import logging

logger = logging.getLogger("stt")


async def recognize(attachment_bytes):
    async with aiohttp.ClientSession() as sess:
        async with sess.post(
            "https://stt.api.cloud.yandex.net/speech/v1/stt:recognize",
            data=attachment_bytes,
            headers={"Authorization": f"Api-Key {config.yandex_stt_token}"},
        ) as resp:
            res = await resp.json()
            spoken = res["result"]
            logger.info(f"Recognized text: {spoken}")
            return spoken
