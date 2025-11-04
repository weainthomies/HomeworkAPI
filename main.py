from functions import (
    get_img, check_filename,
    save_metadata, upload_file
)

while True:
    text = input('введите текст картинки: ')
    response = get_img(text)
    if response is None:
        continue

    filename = f'{text}.jpg'
    if not check_filename(filename, response):
        continue

    save_metadata(filename, response)
    upload_file(filename)
