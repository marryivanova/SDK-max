# MaxBot SDK - Полная документация

## Оглавление

1. [Обзор](#обзор)
2. [Установка](#установка)
3. [Быстрый старт](#быстрый-старт)
4. [Основной клиент](#основной-клиент)
5. [API модули](#api-модули)
   - [Bots API](#bots-api)
   - [Messages API](#messages-api)
   - [Callbacks API](#callbacks-api)
   - [Chats API](#chats-api)
   - [Chat Members API](#chat-members-api)
   - [Pin Messages API](#pin-messages-api)
   - [Media API](#media-api)
   - [Subscriptions API](#subscriptions-api)
   - [Updates API](#updates-api)
6. [Примеры использования](#примеры-использования)
7. [Обработка ошибок](#обработка-ошибок)
8. [Логирование](#логирование)
9. [Разработка](#разработка)

---

## Обзор

**MaxBot SDK** — это Python библиотека для взаимодействия с MaxBot API. Библиотека предоставляет полный набор инструментов для создания ботов на платформе Max.ru с использованием современного асинхронного Python.

### Основные возможности

✅ **Полный набор методов MaxBot API** — Все доступные методы API реализованы в SDK  
🚀 **Асинхронные методы с поддержкой async/await** — Высокая производительность  
🛡️ **Строгая типизация и валидация данных** — Надежность и предсказуемость  
📊 **Встроенное логирование всех запросов и ответов** — Упрощенная отладка  
🔄 **Управление HTTP сессиями** — Оптимизация соединений  
🎯 **Упрощенные методы для частых операций** — Удобный API  
⚡ **Поддержка контекстных менеджеров** — Автоматическое управление ресурсами  

---

## Установка

### Установка через pip
```bash
pip install max-sdk
## Getting started

Быстрый старт

Для создания экземпляра класса MaxClient требуются 2 аргумента:

- base_url: Домен MAX API
- access_token: Токен для аутентификации

# Минимальный пример

import asyncio
from max_sdk import MaxClient

async def main():
    async with MaxClient(
        access_token="ВАШ_ТОКЕН",
        base_url="https://platform-api.max.ru",
    ) as client:
        # Получаем информацию о боте
        bot_info = await client.bots.get_my_info()
        print(f"Бот: {bot_info.get('name')}")
        
        # Создаем глубокую ссылку
        deep_link = await client.bots.create_deep_link(
            payload={"action": "start", "ref": "my_ref"}
        )
        print(f"Ссылка: {deep_link}")

if __name__ == "__main__":
    asyncio.run(main())
```

### Доступные API модули

```python
client.bots              # MaxBotsApi - работа с ботами
client.messages          # MaxMessagesApi - отправка сообщений
client.callbacks         # MaxCallbacksApi - обработка колбэков
client.chats             # MaxChatsApi - управление чатами
client.chat_members      # MaxChatMembersApi - участники чатов
client.pin_messages      # MaxPinMessagesApi - закрепленные сообщения
client.media             # MaxMediaApi - работа с медиа
client.subscriptions     # MaxSubscriptionsApi - подписки
client.updates           # MaxUpdatesApi - обновления
```

# API модули

## Bots API

Класс **MaxBotsApi** предоставляет методы для работы с ботами.

### Методы

#### `get_my_info()`
Получение информации о текущем боте.

```python
bot_info = await client.bots.get_my_info()
print(f"ID: {bot_info['user_id']}")
print(f"Имя: {bot_info['name']}")
print(f"Username: {bot_info['username']}")
```

#### `edit_bot_info(bot_patch)`
Изменение информации о боте.

```python
await client.bots.edit_bot_info({
    "first_name": "Новое имя",
    "description": "Новое описание бота",
    "commands": [
        {"name": "start", "description": "Запуск бота"},
        {"name": "help", "description": "Помощь"}
    ]
})
```

#### `create_deep_link(payload, bot_username, base_url, **params)`
Ссылка для бота.

```python
# Простая ссылка
link1 = await client.bots.create_deep_link()

# Ссылка с payload
link2 = await client.bots.create_deep_link(
    payload={"action": "start", "ref": "promo"}
)

# Ссылка с дополнительными параметрами
link3 = await client.bots.create_deep_link(
    payload={"action": "auth"},
    bot_username="@mybot",
    base_url="https://max.ru",
    utm_source="newsletter"
)
```

# Класс MaxMessagesApi

Класс **MaxMessagesApi** предоставляет методы для работы с сообщениями.

## Параметры методов

### `chat_id` (опциональный)
- **Тип:** `int`
- **Описание:** ID чата для получения сообщений

### `message_ids` (опциональный)
- **Тип:** `str` или `List[str]`
- **Описание:** ID сообщений для получения (одиночный или список)

### `start_time` (опциональный)
- **Тип:** `int` или `datetime`
- **Описание:** Начало временного диапазона для фильтрации сообщений

### `end_time` (опциональный)
- **Тип:** `int` или `datetime`
- **Описание:** Конец временного диапазона для фильтрации сообщений

### `count`
- **Тип:** `int`
- **Описание:** Количество возвращаемых сообщений
- **Диапазон:** 1-100
- **Значение по умолчанию:** 50

```python
# Получение сообщений из чата
messages = await client.messages.get_messages(
    chat_id=12345,
    count=30
)

# Получение конкретных сообщений по ID
messages = await client.messages.get_messages(
    message_ids=["msg_001", "msg_002"]
)

# Получение сообщений за период
from datetime import datetime, timedelta
end_time = datetime.now()
start_time = end_time - timedelta(days=7)

messages = await client.messages.get_messages(
    chat_id=12345,
    start_time=start_time,
    end_time=end_time,
    count=50
)
```

## get_message_by_id(message_id)
Получение сообщения по ID.

**Параметры:**
- `message_id` (str) - ID сообщения

```python
message = await client.messages.get_message_by_id("msg_001")
print(message["text"])
```

## send_message(message_body, user_id=None, chat_id=None, disable_link_preview=False)
Отправка сообщения.

**Параметры:**

- **message_body (Dict[str, Any])**  - тело сообщения

- **user_id (int, optional)**  - ID пользователя

- **chat_id (int, optional)**  - ID чата

- **disable_link_preview (bool)**  - отключить предпросмотр ссылок, по умолчанию False

```python
# Отправка в личные сообщения
await client.messages.send_message(
    message_body={
        "text": "Привет!",
        "attachments": []
    },
    user_id=12345
)

# Отправка в групповой чат
await client.messages.send_message(
    message_body={
        "text": "Сообщение в группу",
        "attachments": []
    },
    chat_id=67890,
    disable_link_preview=True
)
```
## edit_message(message_id, message_body)
Редактирование сообщения.

**Параметры:**

- **message_id (str)** - ID сообщения

- **message_body (Dict[str, Any])** - новое тело сообщения

```python
await client.messages.edit_message(
    message_id="msg_001",
    message_body={
        "text": "Исправленный текст",
        "attachments": []
    }
)
```

## delete_message(message_id)
Удаление сообщения.

**Параметры:**

- **message_id (str)** - ID сообщения

```python
await client.messages.delete_message("msg_001")
```

## send_text_message(text, chat_id=None, user_id=None, format_type=None, attachments=None, disable_link_preview=False, notify=True)
Упрощенная отправка текстового сообщения.

**Параметры:**

- **text (str)** - текст сообщения

- **chat_id (int, optional)** - ID чата

- **user_id (int, optional)** - ID пользователя

- **format_type (str, optional)** - форматирование текста

- **attachments (List[Dict], optional)** - вложения

- **disable_link_preview (bool)** - отключить предпросмотр ссылок

- **notify (bool)** - отправлять уведомление, по умолчанию True

```python
# Простое текстовое сообщение
await client.messages.send_text_message(
    text="Привет, мир!",
    chat_id=12345
)

# Сообщение с форматированием и вложениями
await client.messages.send_text_message(
    text="*Важное* сообщение",
    format_type="markdown",
    attachments=[{"type": "image", "url": "https://example.com/image.jpg"}],
    disable_link_preview=True
)
```
