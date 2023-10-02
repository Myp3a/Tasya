import aiohttp
import config

async def caption(b64_str):
    async with aiohttp.ClientSession() as sess:
        async with sess.post(config.caption_api, json={"image": b64_str}) as resp:
            res = await resp.json()
            capt = res["caption"]
            return capt
