from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from max_sdk.core.max_core import MaxApi


def convert_to_timestamp(time_value: Union[int, datetime]) -> int:
    if isinstance(time_value, datetime):
        return int(time_value.timestamp())
    elif isinstance(time_value, (int, float)):
        return int(time_value)


class MaxMessagesApi(MaxApi):

    async def get_messages(
        self,
        chat_id: Optional[int] = None,
        message_ids: Optional[Union[str, List[str]]] = None,
        start_time: Optional[Union[int, datetime]] = None,
        end_time: Optional[Union[int, datetime]] = None,
        count: int = 50,
    ) -> Dict[str, Any]:
        """
        Получение сообщений
        """
        if chat_id is None and message_ids is None:
            raise ValueError("Требуется указать chat_id или message_ids")

        params = {"count": min(max(count, 1), 100)}

        if chat_id:
            params["chat_id"] = chat_id

        if message_ids:
            if isinstance(message_ids, list):
                params["message_ids"] = ",".join(str(mid) for mid in message_ids)
            else:
                params["message_ids"] = str(message_ids)

        if start_time:
            params["from"] = convert_to_timestamp(start_time)

        if end_time:
            params["to"] = convert_to_timestamp(end_time)

        return await self._make_request("GET", "/messages", params=params)

    async def get_message_by_id(self, message_id: str) -> Dict[str, Any]:
        """
        Получение сообщения по ID
        """
        return await self._make_request("GET", f"/messages/{message_id}")

    async def send_message(
        self,
        message_body: Dict[str, Any],
        user_id: Optional[int] = None,
        chat_id: Optional[int] = None,
        disable_link_preview: bool = False,
    ) -> Dict[str, Any]:
        """
        Отправка сообщения
        """
        params = {}

        if user_id:
            params["user_id"] = user_id

        if chat_id:
            params["chat_id"] = chat_id

        params["disable_link_preview"] = disable_link_preview

        return await self._make_request("POST", "/messages", params=params, body=message_body)

    async def edit_message(self, message_id: str, message_body: Dict[str, Any]) -> Dict[str, Any]:
        """
        Редактирование сообщения
        """
        params = {"message_id": message_id}
        return await self._make_request("PUT", "/messages", params=params, body=message_body)

    async def delete_message(self, message_id: str) -> Dict[str, Any]:
        """
        Удаление сообщения
        """
        params = {"message_id": message_id}
        return await self._make_request("DELETE", "/messages", params=params)

    async def send_text_message(
        self,
        text: str,
        chat_id: Optional[int] = None,
        user_id: Optional[int] = None,
        format_type: Optional[str] = None,
        attachments: Optional[List[Dict]] = None,
        disable_link_preview: bool = False,
        notify: bool = True,
    ) -> Dict[str, Any]:
        """
        Упрощенная отправка текстового сообщения
        """
        message_body = {
            "text": text,
            "attachments": attachments or [],
            "notify": notify,
        }

        if format_type:
            message_body["format"] = format_type

        return await self.send_message(
            message_body=message_body,
            user_id=user_id,
            chat_id=chat_id,
            disable_link_preview=disable_link_preview,
        )

    async def send_message_with_keyboard(
        self,
        text: str,
        buttons: List[List[Dict[str, Any]]],
        chat_id: Optional[int] = None,
        user_id: Optional[int] = None,
        format_type: Optional[str] = None,
        disable_link_preview: bool = False,
        notify: bool = True,
    ) -> Dict[str, Any]:
        """
        Отправка сообщения с inline клавиатурой

        Args:
            text: Текст сообщения
            buttons: Массив кнопок клавиатуры
            chat_id: ID чата (опционально)
            user_id: ID пользователя (опционально)
            format_type: Формат текста ("markdown" или "html")
            disable_link_preview: Отключить превью ссылок
            notify: Уведомлять участников чата

        Returns:
            Ответ от API
        """
        message_body = {
            "text": text,
            "attachments": [{"type": "inline_keyboard", "payload": {"buttons": buttons}}],
            "disable_link_preview": disable_link_preview,
            "notify": notify,
        }

        if format_type:
            message_body["format"] = format_type

        return await self.send_message(message_body=message_body, user_id=user_id, chat_id=chat_id)
