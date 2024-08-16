from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
import redis
import config
import httpx
from urllib.parse import urlencode
from tools import utils


class ProxyProvider(ABC):
    @abstractmethod
    def get_proxies(self, num: int) -> List[Dict]:
        pass


class IpInfoModel(BaseModel):
    ip: str = Field(title="ip")
    port: int = Field(title="端口")
    user: str = Field(title="IP代理认证的用户名")
    protocol: str = Field(default="https", title="代理IP的协议")
    password: str = Field(title="IP代理认证用户的密码")
    expired_time_ts: Optional[int] = Field(title="IP 过期时间")


class RedisDbIpCache:
    def __init__(self):
        self.redis_client = redis.Redis(host=config.REDIS_DB_HOST, password=config.REDIS_DB_PWD)

    def set_ip(self, ip_key: str, ip_value_info: str, ex: int):
        self.redis_client.set(key=ip_key, value=ip_value_info, ex=ex)

    def load_all_ip(self, proxy_brand_name: str) -> List[IpInfoModel]:
        all_ip_list: List[IpInfoModel] = []
        all_ip_keys: List[str] = self.redis_client.keys(pattern=f"{proxy_brand_name}_*")

        try:
            for ip_key in all_ip_keys:
                ip_value = self.redis_client.get(ip_key)
                if not ip_value:
                    continue
        except Exception as e:
            pass
        return all_ip_list


class JiSuHttpProxy(ProxyProvider):
    def __init__(self, key: str, crypto: str, time_validity_period: int):
        self.proxy_brand_name = "JISUHTTP"
        self.api_path = "https://api.jisuhttp.com"
        self.params = {
            "key": key,
            "crypto": crypto,
            "time": time_validity_period,  # IP使用时长，支持3、5、10、15、30分钟时效
            "type": "json",  # 数据结果为json
            "port": "2",  # IP协议：1:HTTP、2:HTTPS、3:SOCKS5
            "pw": "1",  # 是否使用账密验证， 1：是，0：否，否表示白名单验证；默认为0
            "se": "1",  # 返回JSON格式时是否显示IP过期时间， 1：显示，0：不显示；默认为0
        }
        self.ip_cache = RedisDbIpCache()

    async def get_proxies(self, num: int) -> List[Dict]:
        ip_cache_list = self.ip_cache.load_all_ip(proxy_brand_name=self.proxy_brand_name)
        if len(ip_cache_list) >= num:
            return ip_cache_list[:num]
        ip_infos = []
        async with httpx.AsyncClient() as client:
            url = self.api_path + "/fetchips" + '?' + urlencode(self.params)
            response = await client.get(url, headers={
                "User-Agent": "MediaCrawler https://github.com/NanmiCoder/MediaCrawler"})
            res_dict: Dict = response.json()
            if res_dict.get("code") == 0:
                data: List[Dict] = res_dict.get("data")
                current_ts = utils.get_unix_timestamp()
                for ip_item in data:
                    ip_info_model = IpInfoModel(
                        ip=ip_item.get("ip"),
                        port=ip_item.get("port"),
                        user=ip_item.get("user"),
                        password=ip_item.get("pass"),
                        expired_time_ts=utils.get_unix_time_from_time_str(ip_item.get("expire"))
                    )
                    ip_key = f"JISUHTTP_{ip_info_model.ip}_{ip_info_model.port}_{ip_info_model.user}_{ip_info_model.password}"
                    ip_value = ip_info_model.model_dump_json()
                    ip_infos.append(ip_info_model)
                    self.ip_cache.set_ip(ip_key, ip_value, ex=ip_info_model.expired_time_ts - current_ts)
            else:
                pass
        return ip_cache_list + ip_infos
