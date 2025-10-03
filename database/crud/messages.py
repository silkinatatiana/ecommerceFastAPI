from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import Messages
from database.crud.decorators import handle_db_errors


@handle_db_errors
async def create_message(db: AsyncSession,
                         sender_id: int,
                         chat_id: int,
                         message: str
):
    message_item = Messages(
        chat_id=chat_id,
        message=message,
        sender_id=sender_id
    )
    db.add(message_item)
    await db.commit()


@handle_db_errors
async def get_message(db: AsyncSession,
                      chat_id: int = None,
                      limit: int = None,
                      offset: int = None,
                      sort_asc: bool = False,
                      sort_desc: bool = False
):
    query = select(Messages)

    if chat_id:
        query = query.where(Messages.chat_id == chat_id)

    if sort_asc:
        query = query.order_by(Messages.created_at.asc())

    if sort_desc:
        query = query.order_by(Messages.created_at.desc())

    if limit:
        query = query.limit(limit)

    if offset:
        query = query.offset(offset)

    if limit == 1:
        result = await db.scalar(query)

    else:
        messages = await db.execute(query)
        result = messages.scalars().all()

    return result


