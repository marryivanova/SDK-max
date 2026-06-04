from max_sdk.core.bots import MaxBotsApi
from max_sdk.core.callbacks import MaxCallbacksApi
from max_sdk.core.chat_members import MaxChatMembersApi
from max_sdk.core.chats import MaxChatsApi
from max_sdk.core.max_core import MaxApi
from max_sdk.core.media import MaxMediaApi
from max_sdk.core.messages import MaxMessagesApi
from max_sdk.core.pin_messages import MaxPinMessagesApi
from max_sdk.core.subscriptions import MaxSubscriptionsApi
from max_sdk.core.updates import MaxUpdatesApi


class MaxClient:

    def __init__(
        self,
        access_token: str = "",
        base_url: str = "",
    ):
        self._access_token = access_token
        self._base_url = base_url

        self.base_cls = MaxApi(
            access_token=access_token,
            base_url=base_url,
        )
        self.bots = MaxBotsApi()
        self.chats = MaxChatsApi()
        self.chat_members = MaxChatMembersApi()
        self.pin_messages = MaxPinMessagesApi()
        self.messages = MaxMessagesApi()
        self.media = MaxMediaApi()
        self.callbacks = MaxCallbacksApi()
        self.subscriptions = MaxSubscriptionsApi()
        self.updates = MaxUpdatesApi()

        self._setup_apis()

    def _setup_apis(self):
        for api in [
            self.bots,
            self.chats,
            self.chat_members,
            self.pin_messages,
            self.messages,
            self.media,
            self.callbacks,
            self.subscriptions,
            self.updates,
        ]:
            api.config.access_token = self._access_token
            api.config.base_url = self._base_url
            api._access_token = self._access_token
            api._base_url = self._base_url

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def connect(self):
        for api in [
            self.bots,
            self.chats,
            self.chat_members,
            self.pin_messages,
            self.messages,
            self.media,
            self.callbacks,
            self.subscriptions,
            self.updates,
        ]:
            await api._setup_session()

    async def close(self):
        for api in [
            self.bots,
            self.chats,
            self.chat_members,
            self.pin_messages,
            self.messages,
            self.media,
            self.callbacks,
            self.subscriptions,
            self.updates,
        ]:
            if hasattr(api, "_session") and api._session:
                await api._session.close()
