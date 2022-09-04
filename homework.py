"""Telegram бот для мониторинга статуса домашней работы на ЯП."""


import logging
import os
import sys
import time

import requests
from dotenv import load_dotenv
from telegram import Bot
from telegram import error

import exceptions

load_dotenv()


PRACTICUM_TOKEN = os.getenv('practicum_token')
TELEGRAM_TOKEN = os.getenv('telegram_token')
TELEGRAM_CHAT_ID = os.getenv('telegram_chat_id')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


logging.basicConfig(
    level=logging.INFO,
    filename='program.log',
    format='%(asctime)s, %(levelname)s, %(message)s, %(name)s'
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(stream=sys.stdout)
handler.setFormatter(logging.Formatter(fmt='%(asctime)s, %(levelname)s, '
                                           '%(message)s'))
logger.addHandler(handler)


def send_message(bot, message):
    """Функция для отправки сообщений в чат телеграма."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logger.info(f'Сообщение <{message}> отправлено в ваш чат.')
    except error.TelegramError as specific_error:
        raise exceptions.SendMessageError(f'Сообщение <{message}> '
                                          f'не удалось отправить в '
                                          f'чат в связи с ошибкой:'
                                          f'<{specific_error}>')


def get_api_answer(current_timestamp):
    """Функция для получения ответа от API ЯП."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    try:
        homework_response = requests.get(ENDPOINT,
                                         headers=HEADERS,
                                         params=params
                                         )
    except requests.exceptions.RequestException as specific_error:
        raise exceptions.GetApiAnswer(f'Не удаётся сделать запрос к API '
                                      f'ЯП в связи с ошибкой:'
                                      f'<{specific_error}>')
    response_status_code = homework_response.status_code
    if response_status_code == 200:
        return homework_response.json()
    else:
        raise exceptions.ResponseStatusCode(f'Эндпоинт ЯП недоступен, '
                                            f'код состояния: '
                                            f'{response_status_code}.')


def check_response(response):
    """Функция для проверки ответа API и выдачи данных о последней работе."""
    if not isinstance(response, dict):
        raise TypeError('Ответ API не является словарём.')
    if 'homeworks' in response:
        homeworks = response.get('homeworks')
    else:
        raise KeyError('В ответе API ЯП отсутствует ключ <homeworks>.')
    if 'current_date' not in response:
        raise KeyError('В ответе API ЯН отсутствует ключ <current_date>.')
    if isinstance(homeworks, list):
        return homeworks
    else:
        raise TypeError('Homeworks в ответе API не является списком.')


def parse_status(homework):
    """Функция для выдачи сообщения о статусе последней домашней работы."""
    if isinstance(homework, dict):
        try:
            homework_name = homework.get('homework_name')
        except KeyError:
            raise exceptions.NameIsNone('Имя домашней работы не указано.')
        homework_status = homework.get('status')
        if homework_status in HOMEWORK_VERDICTS:
            verdict = HOMEWORK_VERDICTS[homework_status]
        else:
            raise KeyError('В ответе API ЯП неизвестный '
                           'статус домашней работы.')
        return f'Изменился статус проверки работы "{homework_name}". {verdict}'
    else:
        raise TypeError('Элемент с инф-ей о последней'
                        'работе в ответе API не является словарём.')


def check_tokens():
    """Функция для проверки актуальности токенов."""
    try:
        return all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID])
    except Exception:
        raise exceptions.TokensError('Отсутствует одна из'
                                     'переменных окружения.')


def main():
    """Основная логика работы бота."""
    current_timestamp = int(time.time())
    if check_tokens() is False:
        sys.exit('Токены недоступны.')
    while True:
        try:
            response = get_api_answer(current_timestamp)
            homeworks = check_response(response)
            if homeworks:
                message = parse_status(homeworks[0])
                if homeworks != homeworks[0].get('status'):
                    logger.info('Сообщение отправлено.')
                else:
                    logger.debug('Статус не изменился.')
                    message = 'Статус домашней работы не изменился.'
                send_message(bot, message)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            send_message(bot, message)
            logger.error(message)
        else:
            logger.info('Программа работает без сбоев')
        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    bot = Bot(token=TELEGRAM_TOKEN)
    main()
