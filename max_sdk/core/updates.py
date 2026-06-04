from typing import Any, Dict, List, Optional, Union

from max_sdk.core.max_core import MaxApi


class MaxUpdatesApi(MaxApi):

    async def get_updates(
        self,
        limit: int = 100,
        timeout: int = 30,
        marker: Optional[int] = None,
        types: Optional[Union[str, List[str]]] = None,
    ) -> Dict[str, Any]:
        """
        Получение обновлений
        """
        params = {
            "limit": min(max(limit, 1), 1000),
            "timeout": min(max(timeout, 0), 90),
        }

        if marker:
            params["marker"] = marker

        if types:
            if isinstance(types, list):
                params["update_type"] = ",".join(types)
            else:
                params["update_type"] = types

        return await self._make_request("GET", "/updates", params=params)

    async def get_updates_and_extract_chat_ids(self, limit: int = 100, timeout: int = 30) -> List[int]:
        """
        Получение обновлений и извлечение chat_id
        """
        updates = await self.get_updates(
            limit=limit,
            timeout=timeout,
            types=["message_created", "bot_started", "bot_added"],
        )

        chat_ids = []
        for update in updates.get("updates", []):
            if "chat_id" in update:
                chat_ids.append(update["chat_id"])
            elif "message" in update and "recipient" in update["message"]:
                if "chat_id" in update["message"]["recipient"]:
                    chat_ids.append(update["message"]["recipient"]["chat_id"])
            elif "callback" in update and "message" in update:
                if "recipient" in update["message"]:
                    chat_ids.append(update["message"]["recipient"]["chat_id"])

        return list(set(chat_ids))
