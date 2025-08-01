import requests
import configparser
import json
import re
import time
import sys
from urllib.parse import urlencode, quote
from tqdm import tqdm

config = configparser.ConfigParser(allow_no_value=True, delimiters=("=", ":"))
config.read(['api_keys.ini', 'config.ini'], encoding='utf-8')

def timeit(func):
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        print(f"Время выполнения: {end - start:.1f} сек")
        return result
    return wrapper

def text_transform(text_to_modify) -> list[str]:
    new_text = []
    for text in text_to_modify:
        if not text:
            continue
        text = text.lower()
        while '  ' in text:
            text = text.replace('  ', ' ')
        if text not in new_text:
            new_text.append(text)
    return new_text

class YDConnector:
    """
    Класс для базовых методов работы с пользовательской папкой на Яндекс-диске.
    Методы: create_folder - создание папки;
            delete_folder - удаление папки;
            upload_files - загрузка файлов в папку.
    """
    text_lines = text_transform(config['Cat_Set']['text'].splitlines())
    max_num_of_files = len(text_lines)
    pause_to_check = float(config['Settings']['pause_to_check'])

    def __init__(self):
        self.headers = {'Authorization': f'OAuth {config['Tokens']['YD']}'}
        self.base_url = config['Settings']['target_url']
        self.status_code = 0
        self.status_message = ''

    def create_folder(self) -> None:
        print('Создание папки... ', end='')
        params = {'path': f'{config['Settings']['folder_name']}'}
        response = requests.put(self.base_url, headers=self.headers, params=params)
        self._update_status(response)
        print(f'завершено (статус {self.status_code})')

    def delete_folder(self) -> None:
        print('Удаление папки... ', end='')
        params = {'path': f'{config['Settings']['folder_name']}', 'permanently': 'True'}
        response = requests.delete(self.base_url, headers=self.headers, params=params)
        self._update_status(response)
        if self.status_code == 202:
            print('в процессе... ', end='')
            self._asinc_wait(response)
            print(f'завершено ({self.status_message})')

    @timeit
    def upload_files(self, number_of_files) -> tuple[int, float]:
        number_of_files = min(number_of_files, YDConnector.max_num_of_files)
        YDConnector.text_lines = YDConnector.text_lines[:number_of_files]
        cat_params = {
            'fit': f'{config['Cat_Set']['fit']}',
            'width': f'{config['Cat_Set']['width']}',
            'height': f'{config['Cat_Set']['height']}',
            'font': f'{config['Cat_Set']['font']}',
            'fontSize': f'{config['Cat_Set']['font_size']}',
            }
        pbar = tqdm(total=number_of_files, file=sys.stdout, desc='Копирование')
        all_file_names = []  # Список имен файлов (без расширений) для динамического поиска дублей.
        names_counter = 1  # Счетчик в имя файла для первого дубля.
        for text in YDConnector.text_lines:
            file_name = re.sub(r'[^\w\s]', '', text)
            file_name = file_name.replace(' ', '_').lower()
            # Проверка на наличие дублей, которые могут возникнуть после преобразования текста в имя файла.
            if file_name in all_file_names:
                if (next_file_name := f'{file_name}_1') in all_file_names:
                    # Если уже было имя со счетчиком = 1, то это следующий дубль с тем же текстом.
                    names_counter += 1
                    next_file_name = f'{file_name}_{str(names_counter)}'
                else:
                    names_counter = 1  # Это дубль с новым текстом, нужно сбросить счетчик.
                file_name = next_file_name
            all_file_names.append(file_name)
            file_name += '.jpg'
            pbar.set_postfix_str(f' {file_name}')
            response = requests.post(f'{self.base_url}/upload',
                                     headers=self.headers,
                                     params={'url': f'{config['Settings']['source_url']}{quote(text)}'
                                                    f'?{urlencode(cat_params)}',
                                             'path': f'{config['Settings']['folder_name']}/{file_name}'})
            if not self._update_status(response):
                break
            if self.status_code == 202:
                if not self._asinc_wait(response):
                    print(self.status_code, self.status_message)
                    break
            pbar.update(1)
        pbar.set_postfix_str('Завершено')
        return self._process_files_info()

    def _update_status(self, resp) -> bool:
        self.status_code = resp.status_code
        if self.status_code >= 300:
            if 'application/json' in resp.headers.values():
                self.status_message = resp.json()['message']
            else:
                self.status_message = resp.text
            return False
        else:
            self.status_message = 'OK'
            return True

    def _asinc_wait(self, resp) -> bool:
        link_to_status = resp.json()['href']
        while True:
            response = requests.get(link_to_status, headers=self.headers)
            status = response.json()['status']
            if status == 'in-progress':
                time.sleep(YDConnector.pause_to_check)
            else:
                self.status_code = response.status_code
                self.status_message = status
                return True if status == 'success' else False

    def _process_files_info(self) -> tuple[int, float]:
        response = requests.get(self.base_url,
                                headers=self.headers,
                                params={'path': f'{config['Settings']['folder_name']}',
                                        'fields': '_embedded.items.name,_embedded.items.size,_embedded.items.created'})
        json_data = response.json()['_embedded']['items']
        with open('data.json', 'w', encoding="utf-8") as f:
            json.dump(json_data, f, indent=4, ensure_ascii=False)
        return len(json_data), sum(item['size'] for item in json_data)