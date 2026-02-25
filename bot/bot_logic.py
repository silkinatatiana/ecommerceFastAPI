import logging

from aiogram import Router, types
from aiogram.filters import CommandStart

from bot.kafka.consumer import (
    get_goods_verify_message_ids,
    update_status_line,
)
from bot.kafka.producer import KafkaEventPublisher
from bot.keyboards import Keyboard
from config import Statuses


router = Router()
publisher: KafkaEventPublisher | None = None
logger = logging.getLogger(__name__)


def set_publisher(instance: KafkaEventPublisher) -> None:
    global publisher
    publisher = instance


@router.message(CommandStart())
async def start_command(message: types.Message) -> None:
    await message.answer(
        f"✅ Привет! Твой Telegram ID: {message.from_user.id}.\n"
        "Ожидайте запрос на подтверждение регистрации и выберите: подтвердить или отклонить."
    )


@router.callback_query(lambda c: c.data and c.data.startswith("verify:"))
async def handle_verification_callback(callback: types.CallbackQuery) -> None:
    if publisher is None:
        await callback.answer(
            "⏳ Сервис недоступен, попробуйте позже.", show_alert=True
        )
        logger.error("Kafka publisher is not initialised")
        return

    try:
        _, user_id_str, decision = callback.data.split(":")
        user_id = int(user_id_str)
    except Exception:  # noqa: BLE001
        await callback.answer("Некорректный запрос.", show_alert=True)
        return

    tg_id = callback.from_user.id
    tg_username = callback.from_user.username
    chat_id = callback.message.chat.id if callback.message else None

    if not chat_id:
        await callback.answer("Не удалось определить чат.", show_alert=True)
        return

    await publisher.send_verification_decision(
        user_id=user_id,
        tg_id=tg_id,
        tg_username=tg_username,
        chat_id=chat_id,
        decision=decision,
    )

    text = (
        "✅ Вы подтвердили аккаунт."
        if decision == "approve"
        else "❌ Вы отклонили подтверждение."
    )
    if callback.message:
        await callback.message.edit_text(text)
    await callback.answer(text)


@router.callback_query(lambda c: c.data and c.data.startswith("order_status:"))
async def handle_order_status_callback(callback: types.CallbackQuery) -> None:
    if publisher is None:
        await callback.answer(
            "⏳ Сервис недоступен, попробуйте позже.", show_alert=True
        )
        logger.error("Kafka publisher is not initialised")
        return

    try:
        logger.info(f"Callback data: {callback.data}")
        parts = callback.data.split(":")
        logger.info(f"Callback data parts: {parts}, count: {len(parts)}")
        _, slug, target_status = parts

    except Exception:  # noqa: BLE001
        await callback.answer("Некорректные данные кнопки", show_alert=True)
        return

    chat_id = callback.message.chat.id if callback.message else None

    if not chat_id:
        await callback.answer("Не удалось определить чат", show_alert=True)
        return

    status_label = getattr(Statuses, target_status, target_status)
    if callback.message and callback.message.text:
        new_text = update_status_line(callback.message.text, status_label)
        new_keyboard = Keyboard.build_status_keyboard(slug, status_label)
        try:
            await callback.message.edit_text(
                new_text,
                reply_markup=new_keyboard,
            )
        except Exception as e:  # noqa: BLE001
            logger.warning("Не удалось обновить сообщение заказа: %s", e)

    await publisher.send_order_status_change_request(
        slug=slug, target_status=target_status
    )
    await callback.answer("Запрос на смену статуса отправлен")


@router.callback_query(lambda c: c.data and c.data.startswith("verify_goods:"))
async def handle_verification_goods_callback(callback: types.CallbackQuery) -> None:
    if publisher is None:
        await callback.answer(
            "⏳ Сервис недоступен, попробуйте позже.", show_alert=True
        )
        logger.error("Kafka publisher is not initialised")
        return

    try:
        parts = callback.data.split(":")
        if len(parts) != 4:
            raise ValueError(f"Expected 3 parts, got {len(parts)}")
        _, product_id_str, message_id_str, decision = parts
        product_id, message_id = int(product_id_str), int(message_id_str)
        if decision not in ("approve", "reject"):
            raise ValueError(f"Invalid decision: {decision}")
    except (ValueError, IndexError) as e:
        logger.warning("Invalid goods_verify callback: %r, error: %s", callback.data, e)
        await callback.answer("Некорректный запрос.", show_alert=True)
        return

    await publisher.send_goods_verify_decision(
        product_id=product_id,
        decision=decision,
    )

    status_suffix = (
        "✅ Товар одобрен." if decision == "approve" else "❌ Товар отклонён."
    )
    for (
        chat_id,
        media_msg_id,
        original_caption,
        keyboard_msg_id,
    ) in get_goods_verify_message_ids(product_id):
        try:
            new_caption = f"{original_caption}\n\n{status_suffix}"
            await callback.bot.edit_message_caption(
                chat_id=chat_id,
                message_id=media_msg_id,
                caption=new_caption,
            )
        except Exception as e:
            logger.warning("Не удалось обновить подпись в чате %s: %s", chat_id, e)
        try:
            await callback.bot.delete_message(
                chat_id=chat_id, message_id=keyboard_msg_id
            )
        except Exception as e:
            logger.warning(
                "Не удалось удалить сообщение с кнопками в чате %s: %s", chat_id, e
            )

    await callback.answer("Решение отправлено.")
