from unittest.mock import AsyncMock, patch

import pytest

from max_sdk.main import MaxClient

TEST_ACCESS_TOKEN = "lol_kek_123"
TEST_BASE_URL = "https://lol-kek.max.example.com"


class TestMaxClient:

    def test_initialization(self):
        client = MaxClient(access_token=TEST_ACCESS_TOKEN, base_url=TEST_BASE_URL)

        assert client._access_token == TEST_ACCESS_TOKEN
        assert client._base_url == TEST_BASE_URL
        assert client.base_cls is not None
        assert client.bots is not None
        assert client.chats is not None
        assert client.chat_members is not None
        assert client.pin_messages is not None
        assert client.messages is not None
        assert client.media is not None
        assert client.callbacks is not None
        assert client.subscriptions is not None
        assert client.updates is not None

    def test_initialization_with_defaults(self):
        client = MaxClient()

        assert client._access_token == ""
        assert client._base_url == ""

    def test_setup_apis(self):
        client = MaxClient(access_token=TEST_ACCESS_TOKEN, base_url=TEST_BASE_URL)

        for api in [
            client.bots,
            client.chats,
            client.chat_members,
            client.pin_messages,
            client.messages,
            client.media,
            client.callbacks,
            client.subscriptions,
            client.updates,
        ]:
            assert api.config.access_token == TEST_ACCESS_TOKEN
            assert api.config.base_url == TEST_BASE_URL
            assert api._access_token == TEST_ACCESS_TOKEN
            assert api._base_url == TEST_BASE_URL

    @pytest.mark.asyncio
    async def test_context_manager(self):
        mock_connect = AsyncMock()
        mock_close = AsyncMock()

        with (
            patch.object(MaxClient, "connect", mock_connect),
            patch.object(MaxClient, "close", mock_close),
        ):

            async with MaxClient(access_token=TEST_ACCESS_TOKEN, base_url=TEST_BASE_URL) as client:
                assert isinstance(client, MaxClient)
                mock_connect.assert_called_once()

        mock_close.assert_called_once()

    @pytest.mark.asyncio
    async def test_connect_success(self):
        client = MaxClient(access_token=TEST_ACCESS_TOKEN, base_url=TEST_BASE_URL)

        mock_apis = []
        for api_name in [
            "bots",
            "chats",
            "chat_members",
            "pin_messages",
            "messages",
            "media",
            "callbacks",
            "subscriptions",
            "updates",
        ]:
            mock_api = AsyncMock()
            mock_api._setup_session = AsyncMock()
            setattr(client, api_name, mock_api)
            mock_apis.append(mock_api)

        await client.connect()

        for mock_api in mock_apis:
            mock_api._setup_session.assert_called_once()

        client.chats._setup_session.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_success(self):
        client = MaxClient(access_token=TEST_ACCESS_TOKEN, base_url=TEST_BASE_URL)

        mock_apis = []
        for api_name in [
            "bots",
            "chats",
            "chat_members",
            "pin_messages",
            "messages",
            "media",
            "callbacks",
            "subscriptions",
            "updates",
        ]:
            mock_api = AsyncMock()
            mock_api._session = AsyncMock()
            mock_api._session.close = AsyncMock()
            setattr(client, api_name, mock_api)
            mock_apis.append(mock_api)

        await client.close()

        for mock_api in mock_apis:
            mock_api._session.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_without_session(self):
        client = MaxClient(access_token=TEST_ACCESS_TOKEN, base_url=TEST_BASE_URL)

        mock_api_without_session = AsyncMock()
        delattr(mock_api_without_session, "_session")
        client.bots = mock_api_without_session

        mock_api_with_session = AsyncMock()
        mock_api_with_session._session = AsyncMock()
        mock_api_with_session._session.close = AsyncMock()
        client.chats = mock_api_with_session

        await client.close()

        client.chats._session.close.assert_called_once()

    def test_api_instances_are_unique(self):
        client = MaxClient()

        apis = [
            client.bots,
            client.chats,
            client.chat_members,
            client.pin_messages,
            client.messages,
            client.media,
            client.callbacks,
            client.subscriptions,
            client.updates,
        ]

        for i in range(len(apis)):
            for j in range(i + 1, len(apis)):
                assert apis[i] is not apis[j], f"API objects at index {i} and {j} are the same"

    @pytest.mark.asyncio
    async def test_reconnect_scenario(self):
        client = MaxClient(access_token=TEST_ACCESS_TOKEN, base_url=TEST_BASE_URL)

        for api_name in [
            "bots",
            "chats",
            "chat_members",
            "pin_messages",
            "messages",
            "media",
            "callbacks",
            "subscriptions",
            "updates",
        ]:
            mock_api = AsyncMock()
            mock_api._session = AsyncMock()
            mock_api._session.close = AsyncMock()
            mock_api._setup_session = AsyncMock()
            setattr(client, api_name, mock_api)

        await client.connect()
        await client.close()
        await client.connect()
        await client.close()

        for api_name in [
            "bots",
            "chats",
            "chat_members",
            "pin_messages",
            "messages",
            "media",
            "callbacks",
            "subscriptions",
            "updates",
        ]:
            api = getattr(client, api_name)
            assert api._setup_session.call_count == 2
            assert api._session.close.call_count == 2
