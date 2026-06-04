from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlencode

from max_sdk.core.max_core import MaxApi


class MaxBotsApi(MaxApi):

    async def get_my_info(self) -> Dict[str, Any]:
        """
        Получение информации о текущем боте
        """
        return await self._make_request("GET", "/me")

    async def edit_bot_info(self, bot_patch: Dict[str, Any]) -> Dict[str, Any]:
        """
        Изменение информации о боте

        Args:
            bot_patch: Объект с изменениями (first_name, last_name, description, commands, photo)
        """
        return await self._make_request("PATCH", "/me", body=bot_patch)

    async def set_bot_commands(self, commands: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Установка команд бота

        Args:
            commands: Список команд [{"name": "start", "description": "Запуск бота"}]
        """
        bot_patch = {"commands": commands}
        return await self.edit_bot_info(bot_patch)

    async def update_bot_photo(self, photo_payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Обновление фото бота

        Args:
            photo_payload: Полезная нагрузка для фото (токен или URL)
        """
        bot_patch = {"photo": photo_payload}
        return await self.edit_bot_info(bot_patch)

    async def create_deep_link(
        self,
        payload: Union[str, Dict, None] = None,
        bot_username: Optional[str] = None,
        base_url: str = "https://max.ru",
        **additional_params,
    ) -> str:
        if bot_username is None:
            bot_info = await self.get_my_info()
            bot_username = bot_info.get("username")
            if not bot_username:
                raise ValueError("Не удалось получить username бота")

        query_params = {}

        if payload is not None:
            if isinstance(payload, dict):
                payload_str = urlencode(payload, doseq=True)
            else:
                payload_str = str(payload)

            if len(payload_str) > 512:
                raise ValueError(f"Payload слишком длинный ({len(payload_str)} > 512 символов)")

            query_params["start"] = payload_str

        if additional_params:
            query_params.update(additional_params)

        username_with_at = f"{bot_username.lstrip('@')}"

        if query_params:
            query_string = urlencode(query_params, safe="=")
            deep_link = f"{base_url}/{username_with_at}?{query_string}"
        else:
            deep_link = f"{base_url}/{username_with_at}"

        return deep_link
