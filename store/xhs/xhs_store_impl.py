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
    async def store_comment(self, comment_item: Dict):
        pass

    async def store_content(self, content_item: Dict):
        pass

    async def store_creator(self, creator: Dict):
        pass


class XhsJsonStoreImplement(AbstractStore):
    async def store_comment(self, comment_item: Dict):
        pass

    async def store_content(self, content_item: Dict):
        pass

    async def store_creator(self, creator: Dict):
        pass
