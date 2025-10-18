import requests
import os
from datetime import*
import json
from requests.exceptions import Timeout, RequestException


while True:
    text = input('введите текст картинки: ')


    try:
        url = f"https://cataas.com/cat/says/{text}"
        # Добавляем таймаут для предотвращения зависания
        response = requests.get(url, timeout=20)
    except Timeout:
        print('Превышено время ожидания ответа от сервера. Повторите попытку.')
        continue
    except RequestException as e:
        print(f'Произошла ошибка при запросе: {e}. Попробуйте позже.')
        continue


    filename = f'{text}.jpg'

    # Проверка на дубль названия файла
    try:
        with open(f'{filename}', 'xb') as image_file:
            image_file.write(response.content)
    except FileExistsError:
        print(f"Файл {filename} уже существует")
        continue


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

    while True:
        token = input('введите токен: ')

        # Создаем папку в яндекс диске
        create_folder_url = 'https://cloud-api.yandex.net/v1/disk/resources/'
        params = { 'path': 'FPY-136' }

        headers = {
            'Authorization': f'OAuth {token}'
        }
        response = requests.put(create_folder_url, params=params, headers=headers)

        # Добавляем вывод на случай ошибок, а также пропускаем ответ 409, если папка уже создана
        if not 200 <= response.status_code <= 300 and response.status_code != 409:
            message = response.json()['message']
            if response.status_code == 401:
                print(f'Возникла ошибка: "{message}". Возможно, вы ввели неверный токен.')
            else:
                print(f'Возникла ошибка: "{message}". Повторите свои действия.')
            continue

        # Загружаем файл в облако
        upload_file_url = 'https://cloud-api.yandex.net/v1/disk/resources/upload'
        params = {
            'path': f'FPY-136/{filename}'
        }

        response = requests.get(upload_file_url, params=params, headers=headers )

        if not 200 <= response.status_code <= 300:
            message = response.json()['message']
            print(f'Возникла ошибка: "{message}". Повторите свои действия.')
            continue

        upload_link = response.json()['href']

        with open(filename, 'rb') as f:
            response1 = requests.put(upload_link, files={'file':f})

        if 200 <= response1.status_code <= 300 :
            print(f'файл {filename} успешно загружен в облако')
            break
        else:
            message = response1.json()['message']
            print(f'Возникла ошибка: "{message}". Повторите свои действия.')
