import aiohttp
import random
import asyncio
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star
from astrbot.api import logger
from astrbot.api.message_components import Image, Plain


class YpppImagePlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)

    async def _fetch_image_url(self, session: aiohttp.ClientSession) -> str:
        """获取单张图片的 URL（横竖随机）"""
        if random.random() < 0.5:
            api_url = "https://api.yppp.net/pc.php?return=json"
        else:
            api_url = "https://api.yppp.net/pe.php?return=json"

        timeout = aiohttp.ClientTimeout(total=10)
        async with session.get(api_url, timeout=timeout) as resp:
            if resp.status != 200:
                raise Exception(f"API 状态码 {resp.status}")
            data = await resp.json()
            if data.get("code") != "200":
                raise Exception(f"API 返回错误: {data.get('code')}")
            img_url = data.get("acgurl")
            if not img_url:
                raise Exception("未获取到图片链接")
            return img_url

    @filter.command("图图")
    async def tu_tu(self, event: AstrMessageEvent, params: str = ""):
        """发送随机二次元图片，支持数量参数（合并到一条消息链）"""
        logger.info(f"触发 /图图 指令，参数: {params}")

        # 解析数量参数
        count = 1
        if params and params.strip().isdigit():
            count = int(params.strip())
            if count > 15:
                count = 15
                yield event.plain_result("最多支持15张图片，将发送15张")
            elif count < 1:
                count = 1

        # 先提示正在获取
        yield event.plain_result(f"正在获取 {count} 张图片...")

        # 并发获取所有图片 URL
        urls = []
        async with aiohttp.ClientSession() as session:
            tasks = [self._fetch_image_url(session) for _ in range(count)]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for idx, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"获取第 {idx+1} 张图片失败: {result}")
                else:
                    if result:
                        urls.append(result)

        if not urls:
            yield event.plain_result("所有图片获取失败，请稍后重试")
            return

        # 构建消息链：文字 + 多张图片（按顺序）
        chain = [
            Plain(f"共 {len(urls)} 张图片：")
        ]
        for url in urls:
            chain.append(Image.fromURL(url))

        # 发送一条消息链（AstrBot会尝试作为一条消息发送）
        yield event.chain_result(chain)

    async def terminate(self):
        logger.info("YpppImagePlugin 已卸载")
