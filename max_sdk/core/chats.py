from typing import Any, Dict, Optional

from max_sdk.core.max_core import MaxApi


class MaxChatsApi(MaxApi):

    async def get_chats(self, count: int = 50, marker: Optional[int] = None) -> Dict[str, Any]:
        """
        Получение списка всех групповых чатов
        """
        params = {"count": min(max(count, 1), 100)}
        if marker:
            params["marker"] = marker
        return await self._make_request("GET", "/chats", params=params)

    async def get_chat(self, chat_id: int) -> Dict[str, Any]:
        """
        Получение информации о чате по ID
        """
        return await self._make_request("GET", f"/chats/{chat_id}")

    async def get_chat_by_link(self, chat_link: str) -> Dict[str, Any]:
        """
        Получение чата по ссылке
        """
        chat_link = chat_link.lstrip("@")
        return await self._make_request("GET", f"/chats/{chat_link}")

    async def edit_chat(self, chat_id: int, chat_patch: Dict[str, Any]) -> Dict[str, Any]:
        """
        Изменение информации о чате
        """
        return await self._make_request("PATCH", f"/chats/{chat_id}", body=chat_patch)

    async def delete_chat(self, chat_id: int) -> Dict[str, Any]:
        """
        Удаление чата
        """
        return await self._make_request("DELETE", f"/chats/{chat_id}")

    async def send_action(self, chat_id: int, action: str) -> Dict[str, Any]:
        """
        Отправка действия бота в чат
        """
        body = {"action": action}
        return await self._make_request("POST", f"/chats/{chat_id}/actions", body=body)

    async def typing_on(self, chat_id: int) -> Dict[str, Any]:
        """Показать, что бот печатает"""
        return await self.send_action(chat_id, "typing_on")

    async def mark_seen(self, chat_id: int) -> Dict[str, Any]:
        """Пометить сообщения как прочитанные"""
        return await self.send_action(chat_id, "mark_seen")
