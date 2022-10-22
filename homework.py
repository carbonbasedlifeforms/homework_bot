import logging
from logging.handlers import RotatingFileHandler
import os
import sys
import time
from dotenv import load_dotenv
from http import HTTPStatus

import requests
from telegram import Bot

import exceptions

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

ENV_VARS = (
    'PRACTICUM_TOKEN',
    'TELEGRAM_TOKEN',
    'TELEGRAM_CHAT_ID'
)

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def send_message(bot, message):
    """Отправка сообщения в Telegram."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
    except Exception as error:
        raise exceptions.SendMessageError(
            f'Возникла ошибка при отправке сообщения; '
            f'id чата:{TELEGRAM_CHAT_ID} , текст ошибки: {error}'
        )
    else:
        logging.info('Сообщение отправлено в Telegram')


def get_api_answer(current_timestamp):
    """Отправка запроса к API Yandex Practicum."""
    params = {'from_date': current_timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    except Exception as error:
        raise ConnectionError(
            f'Произошел сбой при подключении к API Yandex Practicum '
            f'с параметрами: '
            f'ENDPOINT: {ENDPOINT}; '
            f'HEADERS: {HEADERS}; '
            f'params: {params}); '
            f'Полученный текст ошибки: {error}')
    else:
        if response.status_code != HTTPStatus.OK:
            raise ConnectionError(
                f'Неуспешный запрос к API Yandex Practicum '
                f'код ответа сервера: {response.status_code}'
            )
        return response.json()


def check_response(response):
    """Проверка ответа API на корректность."""
    if not isinstance(response, dict):
        raise TypeError('Ответ API не является словарем')
    if 'homeworks' not in response:
        raise KeyError('ключ homeworks отсутствует в ответе от API')
    homeworks = response['homeworks']
    if not isinstance(homeworks, list):
        wrongtype = type(homeworks)
        raise TypeError(f'Не верный тип ключа homeworks:{wrongtype}')
    return homeworks


def parse_status(homework):
    """Получения статуса домашней работы."""
    homework_name = homework['homework_name']
    if homework_name is None:
        err_message = 'Пустое значение в имени домашки'
        logging.error(err_message)
        raise exceptions.NoHomeworkNameInResponse(err_message)
    homework_status = homework['status']
    if homework_status not in HOMEWORK_VERDICTS:
        err_message = f'Неизвестный статус домашки: {homework_status}'
        logging.error(err_message)
        raise exceptions.UnknownHomeWorkStatus(err_message)
    verdict = HOMEWORK_VERDICTS[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверка переменных окружения."""
    result = True
    for token in ENV_VARS:
        if globals()[token] is None:
            result = False
            logging.critical(
                f'Не обнаружена переменная окружения {token}'
            )
    return result


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        raise SystemExit(
            'Программа завершена, отсутствует одна или более '
            'переменных окружения'
        )
    bot = Bot(token=str(TELEGRAM_TOKEN))
    current_timestamp = 0
    last_hw_status = None
    last_err_message = None
    while True:
        try:
            response = get_api_answer(current_timestamp)
            homeworks = check_response(response)
            if not homeworks:
                logging.info("Домашнее задание не найдено")
                continue
            homework = homeworks[0]
            if homework['status'] != last_hw_status:
                message = parse_status(homework)
                send_message(bot, message)
                last_hw_status = homework['status']
            else:
                logging.info("Статус домашего задания не изменился")
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logging.error(message)
            if message != last_err_message:
                send_message(bot, message)
                last_err_message = message
        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    logging.basicConfig(
        format=(
            '%(asctime)s '
            '[%(levelname)s] '
            '%(message)s; '
            '%(funcName)s; '
            '%(lineno)s'
        ),
        level=logging.INFO,
        handlers=[
            logging.StreamHandler(stream=sys.stdout),
            RotatingFileHandler(
                filename=f'{__file__}.log',
                mode='a',
                encoding='utf-8',
                maxBytes=52428800,
                backupCount=5
            )
        ],

    )
    main()
