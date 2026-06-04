from typing import Any, Dict

from max_sdk.core.max_core import MaxApi


class MaxCallbacksApi(MaxApi):

    async def answer_on_callback(self, callback_id: str, answer_body: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ответ на callback
        """
        params = {"callback_id": callback_id}
        return await self._make_request("POST", "/answers", params=params, body=answer_body)

    async def send_callback_notification(self, callback_id: str, notification_text: str) -> Dict[str, Any]:
        """
        Отправка уведомления в ответ на callback
        """
        answer_body = {"notification": notification_text}
        return await self.answer_on_callback(callback_id, answer_body)

    async def update_callback_message(self, callback_id: str, message_body: Dict[str, Any]) -> Dict[str, Any]:
        """
        Обновление сообщения в ответ на callback
        """
        answer_body = {"message": message_body}
        return await self.answer_on_callback(callback_id, answer_body)

    async def update_callback_message_and_notify(
        self, callback_id: str, message_body: Dict[str, Any], notification_text: str
    ) -> Dict[str, Any]:
        """
        Обновление сообщения и отправка уведомления
        """
        answer_body = {"message": message_body, "notification": notification_text}
        return await self.answer_on_callback(callback_id, answer_body)
