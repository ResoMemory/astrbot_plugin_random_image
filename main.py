import aiohttp
import random
import asyncio
import json
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star
from astrbot.api import logger
from astrbot.api.message_components import Image, Plain


class RandomImagePlugin(Star):
    def __init__(self, context: Context, config: dict = None):
        super().__init__(context)
        self.config = config or {}
        self.max_count = self.config.get("max_count", 15)
        self.default_count = self.config.get("default_count", 1)
        self.timeout = self.config.get("api_timeout", 10)
        self.orientation = self.config.get("orientation", "random")

        try:
            headers_str = self.config.get("headers_json", "{}")
            self.headers = json.loads(headers_str)
        except json.JSONDecodeError:
            self.headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "application/json"
            }
            logger.warning("headers_json 解析失败，使用默认请求头")

    async def _fetch_image_url(self, session: aiohttp.ClientSession) -> str:
        if self.orientation == "pc":
            api_url = "https://api.yppp.net/pc.php?return=json"
        elif self.orientation == "pe":
            api_url = "https://api.yppp.net/pe.php?return=json"
        else:
            api_url = "https://api.yppp.net/pc.php?return=json" if random.random() < 0.5 else "https://api.yppp.net/pe.php?return=json"

        timeout = aiohttp.ClientTimeout(total=self.timeout)
        async with session.get(api_url, headers=self.headers, timeout=timeout) as resp:
            if resp.status != 200:
                raise Exception(f"API 状态码 {resp.status}")
            data = await resp.json()
            if data.get("code") != "200":
                raise Exception(f"API 返回错误: {data.get('code')}")
            img_url = data.get("acgurl")
            if not img_url:
                raise Exception("未获取到图片链接")
            return img_url

    @filter.command("图图")  # ← 修改此处可更换命令名
    async def tu_tu(self, event: AstrMessageEvent, params: str = ""):
        logger.info(f"触发 /图图 指令，参数: {params}")

        count = self.default_count
        if params and params.strip().isdigit():
            count = int(params.strip())
            if count > self.max_count:
                count = self.max_count
                yield event.plain_result(f"最多支持{self.max_count}张图片，将发送{self.max_count}张")
            elif count < 1:
                count = 1

        if count == 1:
            yield event.plain_result("正在获取图片...")
            try:
                async with aiohttp.ClientSession() as session:
                    img_url = await self._fetch_image_url(session)
                yield event.chain_result([
                    Plain("✨ 你的二次元图片来啦！"),
                    Image.fromURL(img_url)
                ])
            except Exception as e:
                logger.error(f"获取单张图片失败: {e}")
                yield event.plain_result(f"获取图片失败: {str(e)}")
        else:
            yield event.plain_result(f"正在获取 {count} 张图片，请稍候...")

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

            chain = [Plain(f"共 {len(urls)} 张图片：")]
            for url in urls:
                chain.append(Image.fromURL(url))

            yield event.chain_result(chain)

    async def terminate(self):
        logger.info("RandomImagePlugin 已卸载")
