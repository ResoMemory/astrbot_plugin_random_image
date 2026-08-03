import aiohttp
import random
import asyncio
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star
from astrbot.api import logger
from astrbot.api.message_components import Image, Plain, Node


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
        """发送随机二次元图片，支持数量参数（合并转发）"""
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

        if count == 1:
            # ----- 单张模式（不合并） -----
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
            # ----- 多张模式（合并转发） -----
            yield event.plain_result(f"正在获取 {count} 张图片，请稍候...")

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

            # 获取机器人自身信息
            bot_uin = event.message_obj.self_id if hasattr(event.message_obj, 'self_id') else 123456
            bot_name = getattr(event, 'self_name', None) or "Bot"

            # 构建 Node 列表（每个 Node 代表一条子消息）
            nodes = []
            for idx, url in enumerate(urls, start=1):
                node = Node(
                    uin=bot_uin,
                    name=bot_name,
                    content=[
                        Plain(f"图片 {idx}"),
                        Image.fromURL(url)
                    ]
                )
                nodes.append(node)

            # 发送合并转发消息（通过 chain_result 传入 nodes 列表）
            yield event.chain_result(nodes)

    async def terminate(self):
        logger.info("YpppImagePlugin 已卸载")
