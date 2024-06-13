import logging
from fastapi import HTTPException, APIRouter, Depends

from src.services import service_plagiarism
from sqlalchemy.ext.asyncio import AsyncSession
from src.config.database import get_session
import uuid

router = (
    APIRouter(
        tags=["ServiceCheatingCode"],
        responses={404: {"description": "Not found"}}
    )
)

logger = logging.getLogger("ServiceCheatingCode")


@router.post('/check')
async def check_plagiarism(
        document_version: uuid.UUID,
        language: str = "python",
        threshold: float = 0.5,
        async_session: AsyncSession = Depends(get_session),
):
    try:
        return await service_plagiarism.check_plagiarism(
            document_version,
            language,
            threshold,
            async_session
        )

    except Exception as e:
        # Логирование ошибки
        logger.exception("An error occurred: %s", str(e))
        raise HTTPException(status_code=500, detail=f"An error occurred {str(e)}")
