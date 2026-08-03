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

        # 缓存
        self._url_cache = []          # 所有图片 URL 列表
        self._cache_locked = False    # 防止并发刷新

    async def _fetch_all_urls(self) -> list:
        """调用 return=all 获取全部图片 URL 列表"""
        if self.orientation == "pc":
            api_url = "https://api.yppp.net/pc.php?return=all"
        elif self.orientation == "pe":
            api_url = "https://api.yppp.net/pe.php?return=all"
        else:  # random
            # 随机选择横图或竖图接口
            api_url = "https://api.yppp.net/pc.php?return=all" if random.random() < 0.5 else "https://api.yppp.net/pe.php?return=all"

        timeout = aiohttp.ClientTimeout(total=self.timeout)
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url, headers=self.headers, timeout=timeout) as resp:
                if resp.status != 200:
                    raise Exception(f"批量获取失败，状态码 {resp.status}")
                # 返回纯文本，每行一个 URL
                text = await resp.text()
                lines = [line.strip() for line in text.splitlines() if line.strip()]
                if not lines:
                    raise Exception("批量获取返回空列表")
                # 去重
                unique_urls = list(set(lines))
                logger.info(f"获取到 {len(unique_urls)} 张图片（去重后）")
                return unique_urls

    async def _ensure_cache(self):
        """确保缓存中有足够的图片 URL"""
        if len(self._url_cache) < self.max_count:
            if self._cache_locked:
                # 如果正在刷新，等待完成
                await asyncio.sleep(1)
                return
            self._cache_locked = True
            try:
                logger.info("缓存不足，正在刷新图片列表...")
                new_urls = await self._fetch_all_urls()
                if new_urls:
                    self._url_cache = new_urls
                    random.shuffle(self._url_cache)  # 打乱顺序
                else:
                    raise Exception("刷新缓存失败")
            finally:
                self._cache_locked = False

    async def _get_random_urls(self, count: int) -> list:
        """从缓存中随机取出 count 个不重复的 URL（会从缓存中移除）"""
        if not self._url_cache:
            await self._ensure_cache()

        if len(self._url_cache) < count:
            # 缓存不足，强制刷新
            await self._ensure_cache()
            if len(self._url_cache) < count:
                # 仍然不足，返回所有剩余
                urls = self._url_cache.copy()
                self._url_cache.clear()
                return urls

        # 从缓存中随机取 count 个（不重复）
        selected = random.sample(self._url_cache, count)
        # 从缓存中移除这些已使用的 URL
        for url in selected:
            self._url_cache.remove(url)
        return selected

    @filter.command("图图")
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

        # 获取图片 URL（从缓存中取）
        try:
            urls = await self._get_random_urls(count)
        except Exception as e:
            logger.error(f"获取图片 URL 失败: {e}")
            yield event.plain_result(f"获取图片失败: {str(e)}")
            return

        if not urls:
            yield event.plain_result("暂无可用图片，请稍后重试")
            return

        if count == 1:
            # 单张
            yield event.plain_result("✨ 你的二次元图片来啦！")
            yield event.chain_result([Image.fromURL(urls[0])])
        else:
            # 多张
            chain = [Plain(f"共 {len(urls)} 张图片：")]
            for url in urls:
                chain.append(Image.fromURL(url))
            yield event.chain_result(chain)

    async def terminate(self):
        logger.info("RandomImagePlugin 已卸载")
