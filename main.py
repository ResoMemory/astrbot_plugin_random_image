import aiohttp
import random
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star
from astrbot.api import logger
from astrbot.api.message_components import Image, Plain


class YpppImagePlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)

    @filter.command("随机图")
    async def random_image(self, event: AstrMessageEvent):
        """获取一张随机二次元图片"""
        logger.info("触发 /随机图 指令")
        await event.plain_result("正在获取图片，请稍候...")

        try:
            # 随机选择横图或竖图接口
            if random.random() < 0.5:
                api_url = "https://api.yppp.net/pc.php?return=json"
            else:
                api_url = "https://api.yppp.net/pe.php?return=json"

            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession() as session:
                async with session.get(api_url, timeout=timeout) as resp:
                    if resp.status != 200:
                        await event.plain_result(f"获取图片失败，状态码: {resp.status}")
                        return

                    data = await resp.json()
                    if data.get("code") != "200":
                        await event.plain_result(f"API返回错误: {data.get('code')}")
                        return

                    img_url = data.get("acgurl")
                    if not img_url:
                        await event.plain_result("未获取到图片链接")
                        return

                    # 发送图片
                    yield event.chain_result([
                        Plain("✨ 你的二次元图片来啦！"),
                        Image.fromURL(img_url)
                    ])

        except asyncio.TimeoutError:
            await event.plain_result("请求超时，请稍后重试")
        except Exception as e:
            logger.error(f"获取图片失败: {e}")
            await event.plain_result(f"获取图片失败: {str(e)}")

    async def terminate(self):
        """插件卸载时调用"""
        logger.info("YpppImagePlugin 已卸载")
