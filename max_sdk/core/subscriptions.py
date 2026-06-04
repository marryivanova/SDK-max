from typing import Any, Dict, List, Optional

from max_sdk.core.max_core import MaxApi


class MaxSubscriptionsApi(MaxApi):

    async def get_subscriptions(self) -> Dict[str, Any]:
        """
        Получение списка подписок
        """
        return await self._make_request("GET", "/subscriptions")

    async def subscribe(
        self,
        url: str,
        update_types: List[str],
        secret: Optional[str] = None,
        version: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Подписка на обновления
        """
        body = {"url": url, "update_types": update_types}

        if secret:
            body["secret"] = secret

        if version:
            body["version"] = version

        return await self._make_request("POST", "/subscriptions", body=body)

    async def unsubscribe(self, url: str) -> Dict[str, Any]:
        """
        Отписка от обновлений
        """
        params = {"url": url}
        return await self._make_request("DELETE", "/subscriptions", params=params)

    async def subscribe_to_all_updates(self, url: str, secret: Optional[str] = None) -> Dict[str, Any]:
        """
        Подписка на все типы обновлений
        """
        update_types = [
            "message_created",
            "message_callback",
            "message_edited",
            "message_removed",
            "bot_added",
            "bot_removed",
            "bot_started",
            "bot_stopped",
            "user_added",
            "user_removed",
            "chat_title_changed",
            "message_chat_created",
            "dialog_muted",
            "dialog_unmuted",
            "dialog_cleared",
            "dialog_removed",
        ]

        return await self.subscribe(url, update_types, secret)
