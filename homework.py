import logging
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

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

logging.basicConfig(
    handlers=[logging.StreamHandler()],
    format='%(asctime)s [%(levelname)s] %(message)s; %(funcName)s; %(lineno)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def send_message(bot, message):
    """Отправка сообщения в Telegram."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logger.info('Сообщение отправлено в Telegram')
    except Exception as error:
        logger.error(f'Возникла ошибка при отправке сообщения: {error}')


def get_api_answer(current_timestamp):
    """Отправка запроса к API Yandex Practicum."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    if response.status_code != HTTPStatus.OK:
        err_message = (
            f'Неуспешный запрос к API Yandex Practicum'
            f'код ответа сервера: {response.status_code}'
        )
        logger.error(err_message)
        raise exceptions.HTTPStatusOKException(err_message)
    return response.json()


def check_response(response):
    """Проверка ответа API на корректность."""
    if response['homeworks'] is None:
        err_message = 'Отсутствует ключ homeworks в ответе от API'
        logger.error(err_message)
        raise exceptions.HomeworksKeyIsNotExists(err_message)
    if ['homeworks'][0] not in response:
        err_message = 'Нет домашки в респонсе'
        logger.error(err_message)
        raise exceptions.EmptyHomeworkInResponse(err_message)
    homeworks = response['homeworks']
    if isinstance(homeworks, list):
        return homeworks
    else:
        err_message = 'Не верный тип ключа homeworks'
        raise exceptions.WrongTypeOfHomeworksKey(err_message)


def parse_status(homework):
    """Получения статуса домашней работы."""
    homework_name = homework['homework_name']
    if homework_name is None:
        err_message = 'Пустое значение в имени домашки'
        logger.error(err_message)
        raise exceptions.NoHomeworkNameInResponse(err_message)
    homework_status = homework['status']
    if homework_status not in HOMEWORK_STATUSES:
        err_message = f'Неизвестный статус домашки: {homework_status}'
        logger.error(err_message)
        raise exceptions.UnknownHomeWorkStatus(err_message)
    verdict = HOMEWORK_STATUSES[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверка переменных окружения."""
    tokens = [
        ('PRACTICUM_TOKEN', PRACTICUM_TOKEN),
        ('TELEGRAM_TOKEN', TELEGRAM_TOKEN),
        ('TELEGRAM_CHAT_ID', TELEGRAM_CHAT_ID),
    ]
    for name, value in tokens:
        trigger = True
        if value is None:
            trigger = False
            logger.critical(
                f'Проверьте что переменная окружения: {name} определена'
            )
        return trigger


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        sys.exit()
    bot = Bot(token=str(TELEGRAM_TOKEN))
    current_timestamp = int(time.time())
    last_hw_status = 'reviewing'
    first_error_send = True
    while True:
        try:
            response = get_api_answer(current_timestamp)
            homeworks = check_response(response)
            if homeworks:
                homework = homeworks[0]
                if homework['status'] != last_hw_status:
                    message = parse_status(homework)
                    send_message(bot, message)
                    last_hw_status = homework['status']
                else:
                    logger.info("Статус домашего задания не изменился")
            else:
                logger.info("Домашнее задание не найдено")
            current_timestamp = int(time.time())
            time.sleep(RETRY_TIME)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logger.error(message)
            if first_error_send:
                first_error_send = False
                send_message(bot, message)
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
