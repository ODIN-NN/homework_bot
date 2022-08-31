"""Telegram бот для мониторинга статуса домашней работы на ЯП."""


import logging
import os
import sys
import time

import requests
from dotenv import load_dotenv
from telegram import Bot

load_dotenv()


PRACTICUM_TOKEN = os.getenv('practicum_token')
TELEGRAM_TOKEN = os.getenv('telegram_token')
TELEGRAM_CHAT_ID = os.getenv('telegram_chat_id')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_STATUSES = {
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
    except Exception as error:
        logger.error(f'Сообщение <{message}> не удалось отправить '
                     f'в чат в связи с ошибкой:<{error}>')


def get_api_answer(current_timestamp):
    """Функция для получения ответа от API ЯП."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    homework_response = requests.get(ENDPOINT,
                                     headers=HEADERS,
                                     params=params
                                     )
    response_status_code = homework_response.status_code
    if response_status_code == 200:
        homework_dict = homework_response.json()
        return homework_dict
    else:
        logger.error(f'Эндпоинт ЯП недоступен, '
                     f'код состояния: {response_status_code}.')
        raise Exception(f'Эндпоинт ЯП недоступен, '
                        f'код состояния: {response_status_code}.')


def check_response(response):
    """Функция для проверки ответа API и выдачи данных о последней работе."""
    if isinstance(response, dict):
        if isinstance(response['homeworks'], list):
            return response['homeworks']
        else:
            logger.error('Homeworks в ответе API не является списком')
            raise TypeError('Homeworks в ответе API не является списком')

    else:
        logger.error('Ответ API не является словарём')
        raise TypeError('Ответ API не является словарём')


def parse_status(homework):
    """Функция для выдачи сообщения о статусе последней домашней работы."""
    homework_name = homework['homework_name']
    homework_status = homework['status']
    if homework_status is None:
        logger.error('Статус домашней работы недокументирован.')
    verdict = HOMEWORK_STATUSES[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Функция для проверки актуальности токенов."""
    if PRACTICUM_TOKEN and TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
        return True
    else:
        logger.critical('Отсутствует одна из переменных окружения!')


def main():
    """Основная логика работы бота."""
    while check_tokens() is True:
        try:
            current_timestamp = int(time.time())
            response = get_api_answer(current_timestamp)
            result_1 = check_response(response)
            time.sleep(RETRY_TIME)
            response = get_api_answer(current_timestamp)
            result_2 = check_response(response)
            if result_1 != result_2:
                notice = parse_status(result_2)
                send_message(bot, notice)
            else:
                continue
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            send_message(bot, message)
            time.sleep(RETRY_TIME)
            logger.error(message)
        else:
            logger.info('Программа работает без сбоев')


if __name__ == '__main__':
    bot = Bot(token=TELEGRAM_TOKEN)
    main()
