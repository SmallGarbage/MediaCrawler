import asyncio
import os.path
import random

import config
from base.base_crawler import AbstractCrawler
from tools import utils
from proxy.proxy_ip_pool import create_ip_pool, IpInfoModel
from typing import Tuple, Optional, Dict, List
from playwright.async_api import async_playwright, BrowserType, BrowserContext
from .client import XHSClient
from .login import XHSLogin
from .field import SearchNoteType, SearchSortType
from store import xhs as xhs_store
from asyncio import Task


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
            await self.browser_context.add_init_script(path="libs/stealth.min.js")
            await self.browser_context.add_cookies(
                [{
                    'name': "webId",
                    'value': "xxx123",  # any value
                    'domain': ".xiaohongshu.com",
                    'path': "/"
                }]
            )
            self.context_page = await self.browser_context.new_page()
            await self.context_page.goto(self.index_url)

            self.xhs_client = await self.create_xhs_client(httpx_proxy_format)
            if not await self.xhs_client.pong():
                login_obj = XHSLogin(
                    login_type=self.login_type,
                    login_phone="",  # input your phone number
                    browser_context=self.browser_context,
                    context_page=self.context_page,
                    cookie_str=config.COOKIES
                )
                await login_obj.begin()
                await self.xhs_client.update_cookies(browser_context=self.browser_context)

            if self.crawler_type == "search":
                await self.search()

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
    ) -> BrowserContext:
        if config.SAVE_LOGIN_STATE:
            # feat issue #14
            # we will save login state to avoid login every time
            user_data_dir = os.path.join(os.getcwd(), "browser_data",
                                         config.USER_DATA_DIR % self.platform)  # type: ignore
            browser_context = await chromium.launch_persistent_context(
                user_data_dir=user_data_dir,
                accept_downloads=True,
                headless=headless,
                proxy=playwright_proxy,  # type: ignore
                viewport={"width": 1920, "height": 1080},
                user_agent=user_agent
            )
            return browser_context
        else:
            browser = await chromium.launch(headless=headless, proxy=playwright_proxy)  # type: ignore
            browser_context = await browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent=user_agent
            )
            return browser_context

    async def create_xhs_client(self, httpx_proxy: Optional[str]) -> XHSClient:
        cookie_str, cookie_dict = utils.convert_cookies()
        xhs_client_obj = XHSClient(
            proxies=httpx_proxy,
            headers={
                "User-Agent": self.user_agent,
                "Cookie": cookie_str,
                "Origin": "https://www.xiaohongshu.com",
                "Referer": "https://www.xiaohongshu.com",
                "Content-Type": "application/json;charset=UTF-8"
            },
            playwright_page=self.context_page,
            cookie_dict=cookie_dict,
        )
        return xhs_client_obj

    async def search(self) -> None:
        xhs_limit_count = 20
        for keyword in config.KEYWORDS.split(","):
            page = 1
            while page * xhs_limit_count <= config.CRAWLER_MAX_NOTES_COUNT:
                note_id_list: List[str] = []
                notes_res = await self.xhs_client.get_note_by_keyword(
                    keyword=keyword,
                    page=page,
                    sort=SearchSortType(config.SORT_TYPE) if config.SORT_TYPE != '' else SearchSortType.GENERAL
                )
                semaphore = asyncio.Semaphore(config.MAX_CONCURRENCY_NUM)
                task_list = [
                    self.get_note_detail(post_item.get('id'), semaphore)
                    for post_item in notes_res.get("items", {})
                    if post_item.get('model_type') not in ('rec_query', 'hot_query')
                ]
                mote_details = await asyncio.gather(*task_list)
                for note_detail in mote_details:
                    if note_detail is not None:
                        await xhs_store.update_xhs_note(note_detail)
                        note_id_list.append(note_detail.get("note_id"))
                page += 1
                await self.batch_get_note_comments(note_id_list)

    async def get_note_detail(self, note_id: str, semaphore: asyncio.Semaphore) -> Optional[Dict]:
        """get note detail"""
        async with semaphore:
            try:
                return await self.xhs_client.get_note_by_id(note_id)
            except KeyError as ex:
                return None

    async def batch_get_note_comments(self, note_list: List[str]):
        if not config.ENABLE_GET_COMMENTS:
            return
        semaphore = asyncio.Semaphore(config.MAX_CONCURRENCY_NUM)
        task_list: List[Task] = []
        for note_id in note_list:
            task = asyncio.create_task(self.get_comments(note_id, semaphore), name=note_id)
            task_list.append(task)
        await asyncio.gather(*task_list)

    async def get_comments(self, note_id: str, semaphore: asyncio.Semaphore):
        async with semaphore:
            await self.xhs_client.get_note_all_comments(
                note_id=note_id,
                crawl_interval=random.random(),
                callback=xhs_store.batch_update_xhs_note_comments
            )
