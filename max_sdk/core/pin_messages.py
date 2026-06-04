from typing import Any, Dict, Optional

from max_sdk.core.max_core import MaxApi


class MaxPinMessagesApi(MaxApi):

    async def get_pinned_message(self, chat_id: int) -> Dict[str, Any]:
        """
        Получение закреплённого сообщения
        """
        return await self._make_request("GET", f"/chats/{chat_id}/pin")

    async def pin_message(self, chat_id: int, message_id: str, notify: bool = True) -> Dict[str, Any]:
        """
        Закрепление сообщения
        """
        body = {"message_id": message_id, "notify": notify}
        return await self._make_request("PUT", f"/chats/{chat_id}/pin", body=body)

    async def unpin_message(self, chat_id: int) -> Dict[str, Any]:
        """
        Открепление сообщения
        """
        return await self._make_request("DELETE", f"/chats/{chat_id}/pin")

    async def update_chat_pin(self, chat_id: int, message_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Обновление закрепленного сообщения через редактирование чата
        """
        chat_patch = {"pin": message_id}
        return await self._make_request("PATCH", f"/chats/{chat_id}", body=chat_patch)
