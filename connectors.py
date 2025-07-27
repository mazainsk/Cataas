import requests
import configparser
import json
import re
import sys
from tqdm import tqdm
from time import sleep, time
from datetime import datetime

config = configparser.ConfigParser(allow_no_value=True, delimiters=("=", ":"))
config.read(['api_keys.ini', 'config.ini'], encoding='utf-8')
# Можно сделать так, чтобы ключи воспринимались независимо от регистра в их названиях:
# config.optionxform = str

class YDConnector:
    """
    Класс для базовых методов работы с пользовательской папкой на Яндекс-диске.
    Методы: create_folder - создание папки;
            delete_folder - удаление папки;
            upload_files - загрузка файлов в папку.
    """
    text_lines = config['Cat_Set']['Text'].splitlines()
    max_num_of_files = len(text_lines)

    def __init__(self):
        self.headers = {'Authorization': f'OAuth {config['Tokens']['YD']}'}
        self.base_url = config['Settings']['Target_URL']
        self.status_code = 0
        self.status_message = ''

    def create_folder(self):
        print('Создание папки... ', end='')
        params = {'path': f'{config['Settings']['Folder_Name']}'}
        response = requests.put(self.base_url, headers=self.headers, params=params)
        self._update_status(response)
        print(f'завершено (статус {self.status_code})')

    def delete_folder(self):
        print('Удаление папки... ', end='')
        params = {'path': f'{config['Settings']['Folder_Name']}', 'permanently': 'True'}
        response = requests.delete(self.base_url, headers=self.headers, params=params)
        self._update_status(response)
        if self.status_code == 202:
            print('в процессе... ', end='')
            link_to_status = response.json()['href']
            while True:
                response = requests.get(link_to_status, headers=self.headers)
                delete_status = response.json()['status']
                if delete_status == 'in-progress':
                    sleep(0.5)
                else:
                    self.status_code = response.status_code
                    self.status_message = delete_status
                    print(f'завершено ({self.status_message})')
                    break

    def upload_files(self, number_of_files):
        json_data = []
        number_of_files = min(number_of_files, YDConnector.max_num_of_files)
        print(f'Будет скопировано {number_of_files} файлов')
        YDConnector.text_lines = YDConnector.text_lines[:number_of_files]
        params = {
            'fit': f'{config['Cat_Set']['Fit']}',
            'width': f'{config['Cat_Set']['Width']}',
            'height': f'{config['Cat_Set']['Height']}',
            'font': f'{config['Cat_Set']['Font']}',
            'fontSize': f'{config['Cat_Set']['Font_Size']}',
            }
        url_upload_link = f'{self.base_url}/upload'
        pbar = tqdm(total=number_of_files * 10, file=sys.stdout, desc='Копирование',
                    bar_format='{desc}: {percentage:3.0f}%|{bar}| {elapsed}<{remaining}{postfix}')
        for i, text in enumerate(YDConnector.text_lines):
            file_name = re.sub(r'[^\w\s]', '', text)
            file_name = file_name.replace(' ', '_').lower() + '.jpg'
            response = requests.get(f'{config['Settings']['Source_URL']}{text}', params=params)
            pbar.update(3)
            file_content = response.content
            if not self._update_status(response):
                break
            file_size = int(response.headers['Content-Length']) // 1024
            dt_object = datetime.fromtimestamp(time())
            json_data.append({'name': file_name,
                              'size': str(file_size),
                              'time': dt_object.strftime("%Y-%m-%d %H:%M:%S")})
            pbar.set_postfix_str(f' Размер: {file_size} кбайт, Имя: {file_name}')
            pbar.update(4)
            response = requests.get(url_upload_link,
                                    headers=self.headers,
                                    params={'path': f'{config['Settings']['Folder_name']}/{file_name}'})
            if not self._update_status(response):
                break
            url_to_upload = response.json()['href']
            response = requests.put(url_to_upload, files={'file': file_content})
            if not self._update_status(response):
                break
            pbar.update(3)
        pbar.set_postfix_str('Завершено')
        with open('data.json', 'w', encoding="utf-8") as f:
            json.dump(json_data, f, indent=4, ensure_ascii=False)

    def _update_status(self, resp):
        self.status_code = resp.status_code
        if self.status_code >= 300:
            self.status_message = resp.json()['message']
            return False
        else:
            self.status_message = 'OK'
            return True

if __name__ == "__main__":
    pass