import os.path

import config
from base.base_crawler import AbstractCrawler
from tools import utils
from proxy.proxy_ip_pool import create_ip_pool, IpInfoModel
from typing import Tuple, Optional, Dict, List
from playwright.async_api import async_playwright, BrowserType, BrowserContext


class XiaoHongShuCrawler(AbstractCrawler):
    platform: str
    login_type: str
    crawler_type: str

    def __init__(self) -> None:
        self.index_url = "https://www.xiaohongshu.com"
        self.user_agent = utils.get_user_agent

    def init_config(self, platform: str, login_type: str, crawler_type: str) -> None:
        self.platform = platform
        self.login_type = login_type
        self.crawler_type = crawler_type

    async def start(self) -> None:
        playwright_proxy_format, httpx_proxy_format = None, None
        if config.ENABLE_IP_PROXY:
            ip_proxy_pool = await create_ip_pool(config.IP_PROXY_POOL_COUNT, enable_validate_ip=True)
            ip_proxy_info: IpInfoModel = await ip_proxy_pool.get_proxy()
            playwright_proxy_format, httpx_proxy_format = self.format_proxy_info(ip_proxy_info)

        async with async_playwright() as playwright:
            chromium = playwright.chromium
            self.browser_context = await self.launch_browser(
                chromium,
                None,
                self.user_agent,
                headless=config.HEADLESS
            )

    @staticmethod
    def format_proxy_info(ip_proxy_info: IpInfoModel) -> Tuple[Optional[Dict], Optional[Dict]]:
        playwright_proxy = {
            "server": f"{ip_proxy_info.protocol}{ip_proxy_info.ip}:{ip_proxy_info.port}",
            "username": ip_proxy_info.user,
            "password": ip_proxy_info.password,
        }

        httpx_proxy = {
            f"{ip_proxy_info.protocol}": f"http://{ip_proxy_info.user}:{ip_proxy_info.password}@{ip_proxy_info.ip}:{ip_proxy_info.port}"
        }
        return playwright_proxy, httpx_proxy

    async def launch_browser(
            self,
            chromium: BrowserType,
            playwright_proxy: Optional[Dict],
            user_agent: Optional[str],
            headless: bool = True
    ):
        if config.SAVE_LOGIN_STATE:
            user_data_dir = os.path.join(os.getcwd(), 'browser_data', config.USER_DATA_DIR % self.platform)
