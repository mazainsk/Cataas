"""
Курсовая работа «Резервное копирование»
"""

from connectors import YDConnector

print('Копирование фотографий кошек с сайта https://cataas.com/ (Cat as a service) в папку на Яндекс-диске.')
disc_connector = YDConnector()
disc_connector.create_folder()
if disc_connector.status_code == 409:
    print(disc_connector.status_message)
    while (t := input('Перезаписать? (y/n) --> ').lower()) not in ('y', 'n'):
        pass
    if t == 'n':
        print('Операция прервана пользователем')
        exit()
    disc_connector.delete_folder()
    if disc_connector.status_code >= 300:
        print(disc_connector.status_code, disc_connector.status_message)
        exit()
    disc_connector.create_folder()
if disc_connector.status_code == 201:
    print(f'В наличии {YDConnector.max_num_of_files} фраз - это максимальное число файлов для копирования')
    while not (number_of_files := input('Сколько файлов записать? --> ')).isdigit():
        pass
    disc_connector.upload_files(int(number_of_files))
    if disc_connector.status_code < 300:
        print(f'Статус {disc_connector.status_code}:', disc_connector.status_message)
        exit()
print(f'Ошибка {disc_connector.status_code}:', disc_connector.status_message)