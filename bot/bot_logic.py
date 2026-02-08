import logging

from aiogram import Router, types
from aiogram.filters import CommandStart

from bot.kafka_consumer import build_status_keyboard, update_status_line
from bot.kafka_producer import KafkaEventPublisher
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
        "✅ Привет! Твой Telegram ID: {tg_id}.\n"
        "Ожидайте запрос на подтверждение регистрации и выберите: подтвердить или отклонить."
        .format(tg_id=message.from_user.id)
    )


@router.callback_query(lambda c: c.data and c.data.startswith("verify:"))
async def handle_verification_callback(callback: types.CallbackQuery) -> None:
    if publisher is None:
        await callback.answer("⏳ Сервис недоступен, попробуйте позже.", show_alert=True)
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

    text = "✅ Вы подтвердили аккаунт." if decision == "approve" else "❌ Вы отклонили подтверждение."
    if callback.message:
        await callback.message.edit_text(text)
    await callback.answer(text)


@router.callback_query(lambda c: c.data and c.data.startswith("order_status:"))
async def handle_order_status_callback(callback: types.CallbackQuery) -> None:
    if publisher is None:
        await callback.answer("⏳ Сервис недоступен, попробуйте позже.", show_alert=True)
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
        new_keyboard = build_status_keyboard(slug, status_label)
        try:
            await callback.message.edit_text(
                new_text,
                reply_markup=new_keyboard,
            )
        except Exception as e:  # noqa: BLE001
            logger.warning("Не удалось обновить сообщение заказа: %s", e)

    await publisher.send_order_status_change_request(
        slug=slug,
        target_status=target_status
    )
    await callback.answer("Запрос на смену статуса отправлен")