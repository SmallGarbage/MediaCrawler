import asyncio
import functools
import sys

from tools import utils

from base.base_crawler import AbstractLogin
from playwright.async_api import BrowserContext, Page
from typing import Optional
from tenacity import RetryError


class XHSLogin(AbstractLogin):
    def __init__(self,
                 login_type: str,
                 browser_context: BrowserContext,
                 context_page: Page,
                 login_phone: Optional[str] = "",
                 cookie_str: str = ""
                 ):
        self.login_type = login_type
        self.browser_context = browser_context
        self.context_page = context_page
        self.login_phone = login_phone
        self.cookie_str = cookie_str

    async def begin(self):
        """开始登陆小红书"""
        if self.login_type == "qrcode":
            await self.login_by_qrcode()

    async def login_by_qrcode(self):
        qrcode_img_selector = "xpath=//img[@class='qrcode-img']"
        base64_qrcode_img = await utils.find_login_qrcode(
            self.context_page,
            qrcode_img_selector
        )
        if not base64_qrcode_img:
            pass
        current_cookie = await self.browser_context.cookies()
        _, cookie_dict = utils.convert_cookies(current_cookie)
        no_logged_in_session = cookie_dict.get("web_session")
        partial_show_qrcode = functools.partial(utils.show_qrcode, base64_qrcode_img)
        asyncio.get_running_loop().run_in_executor(executor=None, func=partial_show_qrcode)
        try:
            await self.check_login_state(no_logged_in_session)
        except RetryError:
            sys.exit()
        wait_redirect_seconds = 5
        await asyncio.sleep(wait_redirect_seconds)

    async def check_login_state(self, no_logged_in_session: str) -> bool:
        if "请通过验证" in await self.context_page.content():
            pass
        current_cookie = await self.browser_context.cookies()
        _, cookie_dict = utils.convert_cookies(current_cookie)
        current_web_session = cookie_dict.get("web_session")
        if current_web_session != no_logged_in_session:
            return True
        return False
