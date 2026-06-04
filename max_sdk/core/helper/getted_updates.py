from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

from loguru import logger

from ..enums.update import UpdateType
from ..types import UpdateUnion
from ..types.updates.bot_added import BotAdded
from ..types.updates.bot_removed import BotRemoved
from ..types.updates.bot_started import BotStarted
from ..types.updates.bot_stopped import BotStopped
from ..types.updates.chat_title_changed import ChatTitleChanged
from ..types.updates.dialog_cleared import DialogCleared
from ..types.updates.dialog_muted import DialogMuted
from ..types.updates.dialog_remove import DialogRemoved
from ..types.updates.dialog_unmuted import DialogUnmuted
from ..types.updates.message_callback import MessageCallback
from ..types.updates.message_chat_created import MessageChatCreated
from ..types.updates.message_created import MessageCreated
from ..types.updates.message_edited import MessageEdited
from ..types.updates.message_removed import MessageRemoved
from ..types.updates.user_added import UserAdded
from ..types.updates.user_removed import UserRemoved
from ..utils.updates import enrich_event

if TYPE_CHECKING:
    from ...dispatcher import Bot

UPDATE_MODEL_MAPPING = {
    UpdateType.BOT_ADDED: BotAdded,
    UpdateType.BOT_REMOVED: BotRemoved,
    UpdateType.BOT_STARTED: BotStarted,
    UpdateType.CHAT_TITLE_CHANGED: ChatTitleChanged,
    UpdateType.MESSAGE_CALLBACK: MessageCallback,
    UpdateType.MESSAGE_CHAT_CREATED: MessageChatCreated,
    UpdateType.MESSAGE_CREATED: MessageCreated,
    UpdateType.MESSAGE_EDITED: MessageEdited,
    UpdateType.MESSAGE_REMOVED: MessageRemoved,
    UpdateType.USER_ADDED: UserAdded,
    UpdateType.USER_REMOVED: UserRemoved,
    UpdateType.BOT_STOPPED: BotStopped,
    UpdateType.DIALOG_CLEARED: DialogCleared,
    UpdateType.DIALOG_MUTED: DialogMuted,
    UpdateType.DIALOG_UNMUTED: DialogUnmuted,
    UpdateType.DIALOG_REMOVED: DialogRemoved,
}


async def get_update_model(event: dict, bot: "Bot") -> UpdateUnion:
    """
    Создает модель обновления из словаря данных.
    """
    update_type = event.get("update_type")

    if not update_type:
        logger.error(f"Отсутствует update_type в событии: {event}")
        raise ValueError("Отсутствует update_type в событии")

    model_cls = UPDATE_MODEL_MAPPING.get(update_type)

    if not model_cls:
        logger.warning(f"⚠️ Неизвестный тип события: {update_type}")
        raise ValueError(f"Unknown update type: {update_type}")

    logger.debug(f"🔍 Обработка события типа: {update_type}")

    event_object = model_cls(**event)
    enriched_event = await enrich_event(event_object=event_object, bot=bot)
    logger.debug(f"✅ Успешно создана модель: {update_type}")
    return enriched_event


async def process_update_request(events: Union[dict, list], bot: "Bot") -> List[UpdateUnion]:
    """
    Обрабатывает обновления полученные через polling.
    """
    updates: List[UpdateUnion] = []

    if not events:
        logger.error("Пустые события")
        return updates

    if isinstance(events, dict):
        if "updates" in events:
            updates_data = events["updates"]
        else:
            updates_data = [events]
    elif isinstance(events, list):
        updates_data = events

    if not isinstance(updates_data, list):
        logger.error(f"Некорректный формат списка обновлений: {type(updates_data)}")
        return updates

    for i, event_data in enumerate(updates_data):
        try:
            logger.debug(f"Обработка обновления #{i + 1}: {event_data.get('update_type', 'unknown')}")

            update = await get_update_model(event_data, bot)
            updates.append(update)
            logger.info(f"Обработано событие #{i + 1}: {event_data.get('update_type')}")

        except ValueError as e:
            logger.warning(f" Пропущено событие #{i + 1}: {e}")
            continue
        except Exception as e:
            logger.error(f"Ошибка обработки обновления #{i + 1}: {e}")
            continue

    logger.info(f"Обработано {len(updates)} обновлений из {len(updates_data)} полученных")
    return updates


async def process_update_webhook(event_json: dict, bot: "Bot") -> Optional[UpdateUnion]:
    """
    Обрабатывает обновление полученное через вебхук.
    """
    try:
        if not event_json:
            return None

        if isinstance(event_json, dict):
            logger.debug(f"Вебхук типа: {event_json.get('update_type', 'unknown')}")

            if "updates" not in event_json:
                update = await get_update_model(event_json, bot)
                logger.success(f"Вебхук обработан: {update.update_type}")
                return update
            else:
                updates_data = event_json.get("updates", [])
                if updates_data and isinstance(updates_data, list) and len(updates_data) > 0:
                    update = await get_update_model(updates_data[0], bot)
                    logger.success(f"Вебхук обработан: {update.update_type}")
                    return update
                else:
                    logger.error(f"Нет событий в вебхуке")
                    return None

    except ValueError as e:
        logger.warning(f"Неподдерживаемый вебхук: {e}")
        return None
    except Exception as e:
        logger.error(f"Ошибка обработки вебхука: {e}")
        return None
