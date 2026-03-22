from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.crud.decorators import handle_db_errors
from models import File


@handle_db_errors
async def get_file_by_id(db: AsyncSession, file_id: int) -> File | None:
    result = await db.execute(select(File).where(File.id == file_id))
    file = result.unique().scalar_one_or_none()
    return file
