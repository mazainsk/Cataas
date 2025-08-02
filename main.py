"""
Курсовая работа «Резервное копирование»
"""

from yd_connector import YDConnector
import logging



def main():
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s', filename='log.txt',
                        encoding='utf-8')

    logging.debug('Это сообщение для отладки')
    logging.info('Информационное сообщение')
    logging.warning('Предупреждение')
    logging.error('Ошибка')
    logging.critical('Критическая ошибка')

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
        print(f'Максимальное число файлов для копирования: {YDConnector.max_num_of_files}')
        while not (number_of_files := input('Сколько файлов записать? --> ')).isdigit():
            pass
        number_of_files, uploaded_size = disc_connector.upload_files(int(number_of_files))
        if disc_connector.status_code < 300:
            print(f'Статус {disc_connector.status_code} ({disc_connector.status_message})')
            print(f'Загружено файлов: {number_of_files}',
                  f'Общий размер: {uploaded_size / 1024 ** 2:.2f} Мбайт', sep='\n')
            exit()
    print(f'Ошибка {disc_connector.status_code}:', disc_connector.status_message)

if __name__ == '__main__':
    main()