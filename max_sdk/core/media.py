from typing import Any, Dict, Optional

from max_sdk.core.max_core import MaxApi
from max_sdk.core.messages import MaxMessagesApi


class MaxMediaApi(MaxApi):

    async def get_upload_url(self, upload_type: str) -> Dict[str, Any]:
        """
        Получение URL для загрузки файла
        """
        params = {"type": upload_type}
        return await self._make_request("POST", "/uploads", params=params)

    async def get_video_attachment_details(self, video_token: str) -> Dict[str, Any]:
        """
        Получение информации о видео
        """
        return await self._make_request("GET", f"/videos/{video_token}")

    async def send_photo(
        self,
        photo_token: str,
        caption: Optional[str] = None,
        chat_id: Optional[int] = None,
        user_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Отправка фото
        """
        messages_api = MaxMessagesApi()
        messages_api._session = self._session
        messages_api._base_url = self._base_url

        attachments = [{"type": "image", "payload": {"token": photo_token}}]

        return await messages_api.send_text_message(
            text=caption or "",
            chat_id=chat_id,
            user_id=user_id,
            attachments=attachments,
        )

    async def send_video(
        self,
        video_token: str,
        caption: Optional[str] = None,
        chat_id: Optional[int] = None,
        user_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Отправка видео
        """

        messages_api = MaxMessagesApi()
        messages_api._session = self._session
        messages_api._base_url = self._base_url

        attachments = [{"type": "video", "payload": {"token": video_token}}]

        return await messages_api.send_text_message(
            text=caption or "",
            chat_id=chat_id,
            user_id=user_id,
            attachments=attachments,
        )

    async def send_audio(
        self,
        audio_token: str,
        caption: Optional[str] = None,
        chat_id: Optional[int] = None,
        user_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Отправка аудио
        """

        messages_api = MaxMessagesApi()
        messages_api._session = self._session
        messages_api._base_url = self._base_url

        attachments = [{"type": "audio", "payload": {"token": audio_token}}]

        return await messages_api.send_text_message(
            text=caption or "",
            chat_id=chat_id,
            user_id=user_id,
            attachments=attachments,
        )

    async def send_file(
        self,
        file_token: str,
        filename: str,
        caption: Optional[str] = None,
        chat_id: Optional[int] = None,
        user_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Отправка файла
        """

        messages_api = MaxMessagesApi()
        messages_api._session = self._session
        messages_api._base_url = self._base_url

        attachments = [{"type": "file", "payload": {"token": file_token}}]

        return await messages_api.send_text_message(
            text=caption or "",
            chat_id=chat_id,
            user_id=user_id,
            attachments=attachments,
        )
