from typing import Any, Dict, List, Optional

from max_sdk.core.max_core import MaxApi


class MaxChatMembersApi(MaxApi):

    async def get_membership(self, chat_id: int) -> Dict[str, Any]:
        """
        Получение информации о членстве бота
        """
        return await self._make_request("GET", f"/chats/{chat_id}/members/me")

    async def leave_chat(self, chat_id: int) -> Dict[str, Any]:
        """
        Выход бота из чата
        """
        return await self._make_request("DELETE", f"/chats/{chat_id}/members/me")

    async def get_admins(self, chat_id: int) -> Dict[str, Any]:
        """
        Получение списка администраторов
        """
        return await self._make_request("GET", f"/chats/{chat_id}/members/admins")

    async def set_admins(self, chat_id: int, admins: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Назначение администраторов
        """
        body = {"admins": admins}
        return await self._make_request("POST", f"/chats/{chat_id}/members/admins", body=body)

    async def delete_admin(self, chat_id: int, user_id: int) -> Dict[str, Any]:
        """
        Удаление администратора
        """
        return await self._make_request("DELETE", f"/chats/{chat_id}/members/admins/{user_id}")

    async def get_members(
        self,
        chat_id: int,
        user_ids: Optional[List[int]] = None,
        marker: Optional[int] = None,
        count: int = 20,
    ) -> Dict[str, Any]:
        """
        Получение участников чата
        """
        params = {"count": min(max(count, 1), 100)}

        if user_ids:
            params["user_ids"] = ",".join(str(uid) for uid in user_ids)
        elif marker:
            params["marker"] = marker

        return await self._make_request("GET", f"/chats/{chat_id}/members", params=params)

    async def add_members(self, chat_id: int, user_ids: List[int]) -> Dict[str, Any]:
        """
        Добавление участников
        """
        body = {"user_ids": user_ids}
        return await self._make_request("POST", f"/chats/{chat_id}/members", body=body)

    async def remove_member(self, chat_id: int, user_id: int, block: bool = False) -> Dict[str, Any]:
        """
        Удаление участника
        """
        params = {"user_id": user_id, "block": block}
        return await self._make_request("DELETE", f"/chats/{chat_id}/members", params=params)
