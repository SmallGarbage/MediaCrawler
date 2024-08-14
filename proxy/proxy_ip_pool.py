import random
from typing import List

import httpx

from .proxy_ip_provider import IpInfoModel, IpProxy
from tenacity import retry, stop_after_attempt, wait_fixed


class ProxyIpPool:
    def __init__(self, ip_pool_count: int, enable_validate_ip: bool) -> None:
        self.valid_ip_url = "https://httpbin.org/ip"
        self.ip_pool_count = ip_pool_count
        self.enable_validate_ip = enable_validate_ip
        self.proxy_list: List[IpInfoModel] = []

    async def load_proxies(self) -> None:
        self.proxy_list = IpProxy.get_proxies()

    async def is_valid_proxy(self, proxy: IpInfoModel) -> bool:
        """
        验证代理IP是否有效
        :param proxy:
        :return:
        """
        try:
            httpx_proxy = {
                f"{proxy.protocol}": f"http://{proxy.user}:{proxy.password}@{proxy.ip}:{proxy.port}"
            }
            async with httpx.AsyncClient(proxies=httpx_proxy) as client:
                response = await client.get(self.valid_ip_url)
            if response.status_code == 200:
                return True
            else:
                return False
        except Exception as e:
            return e

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(1))
    async def get_proxy(self) -> IpInfoModel:
        if len(self.proxy_list) == 0:
            await self.reload_proxies()

        proxy = random.choice(self.proxy_list)
        if self.enable_validate_ip:
            if not await self.is_valid_proxy(proxy):
                raise Exception("xxxx")
        self.proxy_list.remove(proxy)
        return proxy

    async def reload_proxies(self):
        self.proxy_list = []
        await self.load_proxies()


async def create_ip_pool(ip_pool_count: int, enable_validate_ip: bool) -> ProxyIpPool:
    pool = ProxyIpPool(ip_pool_count, enable_validate_ip)
    await pool.load_proxies()
    return pool
