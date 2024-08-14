import argparse
import asyncio

import config
import db
from base.base_crawler import AbstractCrawler
from media_platform.xhs import XiaoHongShuCrawler


class CrawlerFactory:
    CRAWLERS = {
        "xhs": XiaoHongShuCrawler,
    }

    @staticmethod
    def create_crawler(platform: str) -> AbstractCrawler:
        crawler_class = CrawlerFactory.CRAWLERS.get(platform)
        if not crawler_class:
            raise ValueError("Invalid Media Platform Current only supported xhs or dy or ks or bili ...")
        return crawler_class()


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--platform", choices=["xhs", "dy", "ks", "bili", "wb"], type=str, default=config.PLATFORM,
                        help="Media platform select (xhs | dy | ks | bili | wb)")
    parser.add_argument("--lt", type=str, choices=['qrcode', 'phone', 'cookie'], default=config.LOGIN_TYPE,
                        help="Login type (qrcode | phone | cookie)")
    parser.add_argument('--type', type=str, help='crawler type (search | detail | creator)',
                        choices=["search", "detail", "creator"], default=config.CRAWLER_TYPE)

    args = parser.parse_args()

    if config.SAVE_DATA_OPTION == 'db':
        await db.init_db(create_db=False)

    crawler = CrawlerFactory.create_crawler(platform=args.platform)
    crawler.init_config(
        platform=args.platform,
        login_type=args.lt,
        crawler_type=args.type
    )

    await crawler.start()

    if config.SAVE_DATA_OPTION == 'db':
        await db.close()


if __name__ == '__main__':
    asyncio.run(main())
