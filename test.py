import asyncio

import config


async def search() -> None:
    xhs_limit_count = 20
    for keyword in config.KEYWORDS.split(","):
        page = 1
        while page * xhs_limit_count <= config.CRAWLER_MAX_NOTES_COUNT:
            note_id_list = []
            notes_res = await get_note_by_keyword(
                keyword=keyword,
                page=page,
            )
            semaphore = asyncio.Semaphore(config.MAX_CONCURRENCY_NUM)
            task_list = [
                get_note_detail(post_item.get('id'), semaphore)
                for post_item in notes_res.get('items', {})
                if post_item.get('model_type') not in ('rec_query', 'hot_query')
            ]
            note_details = asyncio.gather(*task_list)
            for note_detail in note_details:
                if note_detail is not None:
                    await update_xhs_store(note_detail)
                    note_id_list.append(note_detail.get("note_id"))

