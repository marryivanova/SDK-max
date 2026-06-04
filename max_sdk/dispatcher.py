from __future__ import annotations

import asyncio
import functools
from asyncio.exceptions import TimeoutError as AsyncioTimeoutError
from typing import TYPE_CHECKING, Any, Awaitable, Callable, Dict, List, Optional, Union

from aiohttp import ClientConnectorError
from loguru import logger

from . import MaxClient
from .core.helper.getted_updates import process_update_request, process_update_webhook
from .core.max_core import MaxApi
from .core.utils.updates import enrich_event

try:
    from fastapi import FastAPI, Request
    from fastapi.responses import JSONResponse

    FASTAPI_INSTALLED = True
except ImportError:
    FASTAPI_INSTALLED = False

try:
    from uvicorn import Config, Server

    UVICORN_INSTALLED = True
except ImportError:
    UVICORN_INSTALLED = False

if TYPE_CHECKING:
    from magic_filter import MagicFilter

from .core.context import MemoryContext
from .core.enums.update import UpdateType
from .core.filters import filter_attrs
from .core.filters.handler import Handler
from .core.types import UpdateUnion
from .core.types.errors import Error

CONNECTION_RETRY_DELAY = 30
GET_UPDATES_RETRY_DELAY = 5


class Bot(MaxClient):
    """Класс бота, наследующий от MaxClient."""

    def __init__(
        self,
        token: str,
        base_url: str = "https://platform-api.max.ru",
        timeout: float = 60.0,
        connect_timeout: float = 10.0,
        auto_requests: bool = True,
        auto_check_subscriptions: bool = True,
    ):
        super().__init__(access_token=token, base_url=base_url)

        for api in [self.bots, self.messages, self.chats, self.updates, self.subscriptions]:
            if hasattr(api, "_session_headers"):
                api._session_headers["Authorization"] = token
                logger.debug(f"Token set for {api.__class__.__name__}")

        self.auto_check_subscriptions = auto_check_subscriptions
        self.auto_requests = auto_requests
        self._me: Optional[Dict[str, Any]] = None
        self.marker_updates: Optional[int] = None

        self.api = MaxApi(
            access_token=token,
            base_url=base_url,
            timeout=timeout,
            connect_timeout=connect_timeout,
            auto_requests=auto_requests,
        )

        self.params = {}

    async def get_me(self) -> Dict[str, Any]:
        if self._me is None:
            response = await self.bots.get_my_info()
            self._me = response
        return self._me

    async def get_updates(
        self,
        limit: int = 100,
        timeout: int = 30,
        marker: Optional[int] = None,
        types: Optional[Union[str, List[str]]] = None,
    ) -> Dict[str, Any]:
        return await self.updates.get_updates(limit=limit, timeout=timeout, marker=marker, types=types)

    async def get_subscriptions(self) -> Dict[str, Any]:
        return await self.subscriptions.get_subscriptions()

    async def send_message(
        self,
        chat_id: int,
        text: str,
        reply_to_msg_id: Optional[int] = None,
        inline_keyboard: Optional[List[List[Dict[str, Any]]]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Отправляет текстовое сообщение.

        Args:
            chat_id: ID чата
            text: Текст сообщения
            reply_to_msg_id: ID сообщения для ответа
            inline_keyboard: Инлайн клавиатура
            **kwargs: Дополнительные параметры

        Returns:
            Ответ от API
        """
        return await self.messages.send_text_message(
            chat_id=chat_id, text=text, reply_to_msg_id=reply_to_msg_id, inline_keyboard=inline_keyboard, **kwargs
        )

    async def get_chat_by_id(self, chat_id: int) -> Dict[str, Any]:
        return await self.chats.get_chat(chat_id=chat_id)

    async def get_event(self, chat_name: str) -> Dict[str, Any]:
        return await self.events.get_event(chat_name=chat_name)

    async def get_chat_member(
        self,
        chat_id: int,
        user_ids: Optional[List[int]] = None,
        marker: Optional[int] = None,
        count: Optional[int] = None,
    ) -> Dict[str, Any]:
        return await self.chat_members.get_members(
            chat_id=chat_id,
            user_ids=user_ids,
            marker=marker,
            count=count,
        )


class BaseMiddleware:
    """Базовый класс для Middleware."""

    async def __call__(
        self,
        handler: Callable[[Any, dict[str, Any]], Awaitable[Any]],
        event_object: Any,
        data: dict[str, Any],
    ) -> Any:
        return await handler(event_object, data)


class Dispatcher:
    """
    Основной класс для обработки событий бота.

    Обеспечивает запуск поллинга и вебхука, маршрутизацию событий,
    применение middleware, фильтров и вызов соответствующих обработчиков.
    """

    def __init__(self, router_id: str | None = None) -> None:
        self.router_id = router_id

        self.event_handlers: List[Handler] = []
        self.contexts: List[MemoryContext] = []
        self.routers: List[Router | Dispatcher] = []
        self.filters: List[MagicFilter] = []
        self.middlewares: List[BaseMiddleware] = []

        self.bot: Optional[Bot] = None
        self.webhook_app: Optional[FastAPI] = None
        self.on_started_func: Optional[Callable] = None
        self.polling = False

        self.message_created = Event(update_type=UpdateType.MESSAGE_CREATED, router=self)
        self.bot_added = Event(update_type=UpdateType.BOT_ADDED, router=self)
        self.bot_removed = Event(update_type=UpdateType.BOT_REMOVED, router=self)
        self.bot_started = Event(update_type=UpdateType.BOT_STARTED, router=self)
        self.bot_stopped = Event(update_type=UpdateType.BOT_STOPPED, router=self)
        self.dialog_cleared = Event(update_type=UpdateType.DIALOG_CLEARED, router=self)
        self.dialog_muted = Event(update_type=UpdateType.DIALOG_MUTED, router=self)
        self.dialog_unmuted = Event(update_type=UpdateType.DIALOG_UNMUTED, router=self)
        self.chat_title_changed = Event(update_type=UpdateType.CHAT_TITLE_CHANGED, router=self)
        self.message_callback = Event(update_type=UpdateType.MESSAGE_CALLBACK, router=self)
        self.message_chat_created = Event(update_type=UpdateType.MESSAGE_CHAT_CREATED, router=self)
        self.message_edited = Event(update_type=UpdateType.MESSAGE_EDITED, router=self)
        self.message_removed = Event(update_type=UpdateType.MESSAGE_REMOVED, router=self)
        self.user_added = Event(update_type=UpdateType.USER_ADDED, router=self)
        self.user_removed = Event(update_type=UpdateType.USER_REMOVED, router=self)
        self.on_started = Event(update_type=UpdateType.ON_STARTED, router=self)

    def webhook_post(self, path: str):
        """Декоратор для регистрации обработчиков вебхука."""

        def decorator(func):
            if self.webhook_app is None:
                if not FASTAPI_INSTALLED:
                    raise ImportError(
                        "\n\t Не установлен fastapi!"
                        "\n\t Выполните команду для установки fastapi: "
                        "\n\t pip install fastapi>=0.68.0"
                        "\n\t Или сразу все зависимости для работы вебхука:"
                        "\n\t pip install maxapi[webhook]"
                    )
                self.webhook_app = FastAPI()

            @self.webhook_app.post(path)
            async def wrapper(request: Request):
                return await func(request)

            return wrapper

        return decorator

    async def check_me(self):
        """Проверяет и логирует информацию о боте."""
        if not self.bot:
            return

        if self.bot._me is None:
            try:
                await self.bot._setup_session()
                self.bot._me = await self.bot.get_me()
            except Exception as e:
                logger.error(f"Ошибка при получении информации о боте: {e}")
                return

        me = self.bot._me
        logger.info(
            f'Бот: @{me.get("username", "unknown")} '
            f'first_name={me.get("first_name", "unknown")} '
            f'id={me.get("user_id", "unknown")}'
        )

    @staticmethod
    def build_middleware_chain(
        middlewares: list[BaseMiddleware],
        handler: Callable[[Any, dict[str, Any]], Awaitable[Any]],
    ) -> Callable[[Any, dict[str, Any]], Awaitable[Any]]:
        """Строит цепочку middleware."""
        for mw in reversed(middlewares):
            handler = functools.partial(mw, handler)
        return handler

    def include_routers(self, *routers: "Router"):
        """Добавляет роутеры."""
        self.routers += [r for r in routers]

    async def __ready(self, bot: Bot):
        """Инициализация перед запуском."""
        self.bot = bot

        try:
            await self.bot._setup_session()
        except Exception as e:
            logger.warning(f"Ошибка настройки сессии: {e}")

        if self.polling and self.bot.auto_check_subscriptions:
            try:
                response = await self.bot.get_subscriptions()
                if isinstance(response, dict) and "subscriptions" in response:
                    subscriptions = response["subscriptions"]
                    if subscriptions:
                        logger_subscriptions_text = ", ".join([s.get("url", str(s)) for s in subscriptions])
                        logger.warning(
                            "БОТ ИГНОРИРУЕТ POLLING! Обнаружены установленные подписки: %s",
                            logger_subscriptions_text,
                        )
            except Exception as e:
                logger.warning(f"Не удалось проверить подписки: {e}")

        await self.check_me()
        self.routers += [self]

        handlers_count = sum(len(router.event_handlers) for router in self.routers)
        logger.info(f"{handlers_count} событий на обработку")

        if self.on_started_func:
            try:
                await self.on_started_func()
            except Exception as e:
                logger.error(f"Ошибка в on_started функции: {e}")

    def __get_memory_context(self, chat_id: int, user_id: int) -> MemoryContext:
        """Получает или создает контекст памяти."""
        for ctx in self.contexts:
            if ctx.chat_id == chat_id and ctx.user_id == user_id:
                return ctx

        new_ctx = MemoryContext(chat_id, user_id)
        self.contexts.append(new_ctx)
        return new_ctx

    @staticmethod
    async def call_handler(handler: Handler, event_object: Any, data: Dict[str, Any]):
        """Вызывает обработчик события."""
        func_args = handler.func_event.__annotations__.keys()
        kwargs_filtered = {k: v for k, v in data.items() if k in func_args}
        await handler.func_event(event_object, **kwargs_filtered)

    async def handle(self, event_object: UpdateUnion):
        """Обрабатывает событие."""
        try:
            ids = event_object.get_ids()
            memory_context = self.__get_memory_context(*ids)
            current_state = await memory_context.get_state()
            kwargs = {"context": memory_context}
            router_id = None

            process_info = f"{event_object.update_type} | chat_id: {ids[0]}, user_id: {ids[1]}"

            if self.bot:
                event_object = await enrich_event(event_object, self.bot)

            is_handled = False

            for index, router in enumerate(self.routers):
                if is_handled:
                    break

                router_id = router.router_id or str(index)

                if router.filters:
                    if not filter_attrs(event_object, *router.filters):
                        continue

                for handler in router.event_handlers:
                    if not handler.update_type == event_object.update_type:
                        continue

                    if handler.filters:
                        if not filter_attrs(event_object, *handler.filters):
                            continue

                    if handler.states:
                        if current_state not in handler.states:
                            continue

                    if isinstance(router, Router):
                        full_middlewares = self.middlewares + router.middlewares + handler.middlewares
                    elif isinstance(router, Dispatcher):
                        full_middlewares = self.middlewares + handler.middlewares

                    handler_chain = self.build_middleware_chain(
                        full_middlewares, functools.partial(self.call_handler, handler)
                    )

                    func_args = handler.func_event.__annotations__.keys()
                    kwargs_filtered = {k: v for k, v in kwargs.items() if k in func_args}

                    await handler_chain(event_object, kwargs_filtered)

                    logger.info(f"Обработано: {router_id} | {process_info}")
                    is_handled = True
                    break

            if not is_handled:
                logger.info(f"Проигнорировано: {router_id} | {process_info}")

        except Exception as e:
            logger.error(f"Ошибка при обработке события: {router_id} | {process_info} | {e}")

    async def start_polling(self, bot: Bot):
        """Запускает поллинг обновлений."""
        self.polling = True
        await self.__ready(bot)

        if self.bot is None:
            raise RuntimeError("Bot не инициализирован")

        while self.polling:
            try:
                updates_response = await self.bot.get_updates()

                if isinstance(updates_response, dict):
                    events = updates_response.get("updates", [])
                    if "marker" in updates_response:
                        self.bot.marker_updates = updates_response["marker"]
                else:
                    events = updates_response

            except AsyncioTimeoutError:
                continue
            except Exception as e:
                logger.error(f"Ошибка получения обновлений: {e}")
                await asyncio.sleep(GET_UPDATES_RETRY_DELAY)
                continue

            try:
                if isinstance(events, Error):
                    logger.warning(f"Ошибка при получении обновлений: {events}, жду {GET_UPDATES_RETRY_DELAY} секунд")
                    await asyncio.sleep(GET_UPDATES_RETRY_DELAY)
                    continue

                processed_events = await process_update_request(events=events, bot=self.bot)

                for event in processed_events:
                    await self.handle(event)

            except ClientConnectorError:
                logger.error(f"Ошибка подключения, жду {CONNECTION_RETRY_DELAY} секунд")
                await asyncio.sleep(CONNECTION_RETRY_DELAY)
            except Exception as e:
                logger.error(f"Общая ошибка при обработке событий: {e.__class__} - {e}")
                await asyncio.sleep(GET_UPDATES_RETRY_DELAY)

    async def handle_webhook(self, bot: Bot, host: str = "localhost", port: int = 8080, **kwargs):
        """Запускает вебхук сервер."""
        if not FASTAPI_INSTALLED:
            raise ImportError(
                "\n\t Не установлен fastapi!"
                "\n\t Выполните команду для установки fastapi: "
                "\n\t pip install fastapi>=0.68.0"
                "\n\t Или сразу все зависимости для работы вебхука:"
                "\n\t pip install maxapi[webhook]"
            )

        elif not UVICORN_INSTALLED:
            raise ImportError(
                "\n\t Не установлен uvicorn!"
                "\n\t Выполните команду для установки uvicorn: "
                "\n\t pip install uvicorn>=0.15.0"
                "\n\t Или сразу все зависимости для работы вебхука:"
                "\n\t pip install maxapi[webhook]"
            )

        @self.webhook_post("/")
        async def webhook_handler(request: Request):
            event_json = await request.json()

            event_object = await process_update_webhook(event_json=event_json, bot=bot)

            if event_object:
                await self.handle(event_object)
            return JSONResponse(content={"ok": True}, status_code=200)

        await self.init_serve(bot=bot, host=host, port=port, **kwargs)

    async def init_serve(self, bot: Bot, host: str = "localhost", port: int = 8080, **kwargs):
        """Инициализирует и запускает сервер."""
        if not UVICORN_INSTALLED:
            raise ImportError(
                "\n\t Не установлен uvicorn!"
                "\n\t Выполните команду для установки uvicorn: "
                "\n\t pip install uvicorn>=0.15.0"
                "\n\t Или сразу все зависимости для работы вебхука:"
            )

        if self.webhook_app is None:
            raise RuntimeError("webhook_app не инициализирован")

        config = Config(app=self.webhook_app, host=host, port=port, **kwargs)
        server = Server(config)

        await self.__ready(bot)
        await server.serve()


class Router(Dispatcher):
    """Класс роутера."""

    def __init__(self, router_id: str | None = None):
        super().__init__(router_id)


class Event:
    """Класс события."""

    def __init__(self, update_type: UpdateType, router: Dispatcher | Router):
        self.update_type = update_type
        self.router = router

    def __call__(self, *args, **kwargs):
        def decorator(func_event: Callable):
            if self.update_type == UpdateType.ON_STARTED:
                self.router.on_started_func = func_event
            else:
                self.router.event_handlers.append(
                    Handler(
                        func_event=func_event,
                        update_type=self.update_type,
                        *args,
                        **kwargs,
                    )
                )
            return func_event

        return decorator
