import asyncio
import csv
import json
import pathlib
import os
import aiofiles

from base.base_crawler import AbstractStore
from typing import Dict
from tools import utils
from tortoise.contrib.pydantic import pydantic_model_creator


class XhsDbStoreImplement(AbstractStore):
    async def store_comment(self, comment_item: Dict):
        from xhs_store_db_types import XHSNoteComment
        comment_id = comment_item.get("comment_id")
        if not await XHSNoteComment.filter(comment_id=comment_id).first():
            comment_item["add_ts"] = utils.get_current_timestamp()
            comment_pydantic = pydantic_model_creator(XHSNoteComment, name="CommentPydanticCreate", exclude=('id',))
            comment_data = comment_pydantic(**comment_item)
            comment_pydantic.model_validate(comment_data)
            await XHSNoteComment.create(**comment_data.model_dump())
        else:
            comment_pydantic = pydantic_model_creator(XHSNoteComment, name="CommentPydanticUpdate",
                                                      exclude=('id', 'add_ts'))
            comment_data = comment_pydantic(**comment_item)
            comment_pydantic.model_validate(comment_data)
            await XHSNoteComment.filter(comment_id=comment_id).update(**comment_data.model_dump())

    async def store_content(self, content_item: Dict):
        from xhs_store_db_types import XHSNote
        note_id = content_item.get("note_id")
        if not await XHSNote.filter(note_id=note_id).first():
            content_item["add_ts"] = utils.get_current_timestamp()
            note_pydantic = pydantic_model_creator(XHSNote, name="XHSPydanticCreate", exclude=('id',))
            note_data = note_pydantic(**content_item)
            note_pydantic.model_validate(note_data)
            await XHSNote.create(**note_data.model_dump())
        else:
            note_pydantic = pydantic_model_creator(XHSNote, name="XHSPydanticUpdate", exclude=('id', 'add_ts'))
            note_data = note_pydantic(**content_item)
            note_pydantic.model_validate(note_data)
            await XHSNote.filter(note_id=note_id).update(**note_data.model_dump())

    async def store_creator(self, creator: Dict):
        pass


class XhsCsvStoreImplement(AbstractStore):
    csv_store_path: str = "data/xhs"

    def make_save_file_name(self, store_type: str) -> str:
        return f"{self.csv_store_path}/{store_type}_{utils.get_current_date()}.csv"

    async def save_data_to_csv(self, save_item: Dict, store_type: str):
        pathlib.Path(self.csv_store_path).mkdir(parents=True, exist_ok=True)
        save_file_name = self.make_save_file_name(store_type=store_type)
        async with aiofiles.open(save_file_name, mode='a+', encoding='utf-8-sig', newline='') as f:
            f.fileno()
            writer = csv.writer(f)
            if await f.tell() == 0:
                await writer.writerow(save_item.keys())
            await writer.writerow(save_item.values())

    async def store_comment(self, comment_item: Dict):
        await self.save_data_to_csv(save_item=comment_item, store_type='contents')

    async def store_content(self, content_item: Dict):
        await self.save_data_to_csv(save_item=content_item, store_type='comments')

    async def store_creator(self, creator: Dict):
        await self.save_data_to_csv(save_item=creator, store_type='creator')


class XhsJsonStoreImplement(AbstractStore):
    json_store_path: str = "data/xhs"
    lock = asyncio.Lock()

    def make_save_file_name(self, store_type: str) -> str:
        return f"{self.csv_store_path}/{store_type}_{utils.get_current_date()}.csv"

    async def save_data_to_json(self, save_item: Dict, store_type: str):
        pathlib.Path(self.json_store_path).mkdir(parents=True, exist_ok=True)
        save_file_name = self.make_save_file_name(store_type=store_type)
        save_data = []
        async with self.lock:
            if os.path.exists(save_file_name):
                async with aiofiles.open(save_file_name, 'r', encoding='utf-8') as file:
                    save_data = json.loads(await file.read())
            save_data.append(save_data)
            async with aiofiles.open(save_file_name, 'w', encoding='utf-8') as file:
                await file.write(json.dumps(save_data, ensure_ascii=False))

    async def store_comment(self, comment_item: Dict):
        pass

    async def store_content(self, content_item: Dict):
        pass

    async def store_creator(self, creator: Dict):
        pass
