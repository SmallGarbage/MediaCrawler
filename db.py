import asyncio

import tortoise
from tortoise import Tortoise, run_async
import config


def get_platform_models():
    models = ["store.xhs"]
    return models


async def init_db(create_db: bool = False) -> None:
    await Tortoise.init(
        db_url=config.RELATION_DB_URL,
        _create_db=create_db,
        modules={'models': get_platform_models()}
    )


async def close() -> None:
    await Tortoise.close_connections()


async def main():
    await init_db(create_db=True)
    await Tortoise.generate_schemas()


if __name__ == '__main__':
    run_async(main())
    # asyncio.run(main())
