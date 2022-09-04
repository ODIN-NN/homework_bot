"""Кастомные исключения для телеграм-бота."""


class SendMessageError(Exception):
    """Исключение при проблемах с отправкой сообщений в чат телеграма."""
    pass


class GetApiAnswer(Exception):
    """Исключение при проблемах с запросом к API ЯП."""
    pass


class ResponseStatusCode(Exception):
    """Исключение при статусе ответа отличном от 200."""
    pass


class CheckResponseError(Exception):
    """Исключение при проверке ключей в запросе."""
    pass


class StatusNone(Exception):
    """Исключение при недокументированном статусе домашней работы."""
    pass


class NameIsNone(Exception):
    """Исключение при пустом имени домашней работы."""
    pass


class TokensError(Exception):
    """Исключение при недоступности одного или нескольких токенов."""
