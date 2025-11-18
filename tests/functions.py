from httpx import AsyncClient
from pydantic import BaseModel, ValidationError
from typing import Type, Any, Dict, Optional, Tuple
import json

from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import fake


def validate_json_response(json_data: Dict[str, Any],
                           schema_class: Type[BaseModel]) -> Tuple[bool, Optional[BaseModel], Optional[str]]:
    try:
        model = schema_class(**json_data)
        return True, model, None
    except ValidationError as e:
        error_messages = []
        for error in e.errors():
            field = " -> ".join(str(loc) for loc in error['loc'])
            error_messages.append(f"{field}: {error['msg']} ({error['type']})")
        return False, None, "; ".join(error_messages)
    except Exception as e:
        return False, None, f"Unexpected error: {str(e)}"
