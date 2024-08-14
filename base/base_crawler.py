from abc import ABC, abstractmethod
from playwright.async_api import async_playwright, BrowserContext, BrowserType
from typing import Optional, Dict, Tuple, List


class AbstractCrawler(ABC):

    @abstractmethod
    def init_config(self, platform: str, login_type: str, crawler_type: str):
        pass

    @abstractmethod
    async def start(self):
        pass

    @abstractmethod
    async def search(self):
        pass

    @abstractmethod
    async def launch_browser(self, chromium: BrowserType, playwright_proxy: Optional[Dict], user_agent: Optional[str],
                             headless: bool = True) -> None:
        pass
