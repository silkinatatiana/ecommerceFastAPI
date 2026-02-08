from typing import Any

from pydantic import BaseModel, ValidationError


def validate_json_response(
    json_data: dict[str, Any], schema_class: type[BaseModel]
) -> tuple[bool, BaseModel | None, str | None]:
    try:
        model = schema_class(**json_data)
        return True, model, None
    except ValidationError as e:
        error_messages = []
        for error in e.errors():
            field = " -> ".join(str(loc) for loc in error["loc"])
            error_messages.append(f"{field}: {error['msg']} ({error['type']})")
        return False, None, "; ".join(error_messages)
    except Exception as e:
        return False, None, f"Unexpected error: {str(e)}"
