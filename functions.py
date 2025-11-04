import requests
import os
from datetime import datetime
import json
from requests.exceptions import Timeout, RequestException

_saved_token = None

def get_img(text):
    """Получает изображение с cataas.com"""

    try:
        url = f"https://cataas.com/cat/says/{text}"
        # Добавляем таймаут для предотвращения зависания
        return requests.get(url, timeout=20)
    except Timeout:
        print('Превышено время ожидания ответа от сервера. Повторите попытку.')
        return None
    except RequestException as e:
        print(f'Произошла ошибка при запросе: {e}. Попробуйте позже.')
        return None

def check_filename(filename, response):
    """Проверяет, существует ли файл. Если нет — создаёт."""

    try:
        with open(f'{filename}', 'xb') as image_file:
            image_file.write(response.content)
        return True
    except FileExistsError:
        print(f"Файл {filename} уже существует")
        return False

def save_metadata(filename, response):
    """Сохраняет метаданные изображения в metadata.json."""

    metadata_path = 'metadata.json'
    all_metadata = []

    # Проверяем, существует ли файл
    if os.path.exists(metadata_path):
        with open(metadata_path, 'r', encoding='utf-8') as json_file:
            all_metadata = json.load(json_file)

    all_metadata.append({
        "filename": filename,
        "contentType": response.headers.get('Content-Type'),
        "contentLength": response.headers.get('Content-Length'),
        "date": datetime.now().isoformat(),
        "additionalInfo": {
            "status_code": response.status_code,
            "encoding": response.encoding
        }
    })

    # Сохраняем метаданные в json-файл
    with open(metadata_path, 'w', encoding='utf-8') as json_file:
        json.dump(all_metadata, json_file, ensure_ascii=False, indent=4)
    return

def _validate_token(token):
    """Проверяет токен и создаёт папку, если её нет.
    Возвращает True, если токен валиден."""

    folder_url = 'https://cloud-api.yandex.net/v1/disk/resources/'
    params = { 'path': 'FPY-136' }
    headers = {
        'Authorization': f'OAuth {token}'
    }
    response = requests.put(folder_url, params=params, headers=headers)
    if 200 <= response.status_code <= 300 or response.status_code == 409:
        return True
    elif response.status_code == 401:
        print('Возникла ошибка 401. Возможно, вы ввели неверный токен.')
        return False
    else:
        message = response.json()['message']
        print(f'Возникла ошибка: "{message}". Повторите свои действия.')
        return False

def _get_valid_token():
    """Запрашивает токен у пользователя до 3 попыток.
    Сохраняет в saved_token, если валиден."""

    global _saved_token
    attempts = 0
    while attempts < 3:
        token = input('Введите токен: ')
        if _validate_token(token):
            _saved_token = token
            return True
        attempts += 1

    print("Превышено число попыток. Завершаем работу.")
    return False

def upload_file(filename):
    """Загружает файл на Яндекс Диск, используя сохранённый токен."""

    global _saved_token

    if _saved_token is None:
        if not _get_valid_token():
            return False

    headers = {'Authorization': f'OAuth {_saved_token}'}
    upload_url = 'https://cloud-api.yandex.net/v1/disk/resources/upload'
    params = {'path': f'FPY-136/{filename}'}

    # Получаем ссылку для загрузки
    try:
        response = requests.get(upload_url, params=params, headers=headers, timeout=10)
        if not (200 <= response.status_code < 300):
            message = response.json().get('message', 'Неизвестная ошибка')
            print(f"Ошибка при получении ссылки для загрузки: {message}")
            return False

        upload_link = response.json()['href']

        # Загружаем файл
        with open(filename, 'rb') as f:
            response_upload = requests.put(upload_link, files={'file': f}, timeout=10)

        if 200 <= response_upload.status_code < 300:
            print(f'Файл {filename} успешно загружен в облако')
            return True
        else:
            message = response_upload.json().get('message', 'Неизвестная ошибка')
            print(f"Ошибка при загрузке файла: {message}")
            return False

    except RequestException as e:
        print(f"Сетевая ошибка при загрузке: {e}")
        return False

