from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from config import Statuses


class Keyboard:
    @staticmethod
    def build_keyboard_verify_account(user_id) -> InlineKeyboardMarkup | None:
        """Собирает клавиатуру для верификации нового аккаунта."""
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="✅ Подтвердить",
                        callback_data=f"verify:{user_id}:approve",
                    ),
                    InlineKeyboardButton(
                        text="❌ Отклонить",
                        callback_data=f"verify:{user_id}:reject",
                    ),
                ]
            ]
        )
        return keyboard

    @staticmethod
    def build_status_keyboard(
        slug: str, current_status_text: str | None
    ) -> InlineKeyboardMarkup | None:
        """Собирает клавиатуру доступных переходов по статусу заказа."""
        if not current_status_text:
            return None

        next_status_key = next(
            (
                status_key
                for status_key, prev_status in Statuses.changing_statuses.items()
                if prev_status == current_status_text
            ),
            None,
        )

        buttons_row = []

        if next_status_key:
            next_label = getattr(Statuses, next_status_key, next_status_key)
            buttons_row.append(
                InlineKeyboardButton(
                    text=f"🔄{next_label}",
                    callback_data=f"order_status:{slug}:{next_status_key}",
                )
            )

        if current_status_text == Statuses.DESIGNED:
            buttons_row.append(
                InlineKeyboardButton(
                    text="❌ Отменить", callback_data=f"order_status:{slug}:CANCELLED"
                )
            )

        if not buttons_row:
            return None

        return InlineKeyboardMarkup(inline_keyboard=[buttons_row])

    @staticmethod
    def build_keyboard_verify_goods(
        product_id: int, message_id: int
    ) -> InlineKeyboardMarkup | None:
        """Собирает клавиатуру для верификации нового товара."""
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="✅ Подтвердить",
                        callback_data=f"verify_goods:{product_id}:{message_id}:approve",
                    ),
                    InlineKeyboardButton(
                        text="❌ Отклонить",
                        callback_data=f"verify_goods:{product_id}:{message_id}:reject",
                    ),
                ]
            ]
        )
        return keyboard
