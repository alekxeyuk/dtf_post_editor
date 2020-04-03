import glob
import json
import string
from io import BytesIO
from random import choice

import pyqrcode
import requests
from PIL import Image

class Post:
    """
        Класс для создания поста на DTF

        __init__:

        :str: Название поста, можно оставить пустым

        :int: ID подсайта для публикации
    """
    def __init__(self, title: str = '', subsite_id: int = 132168):
        self.user_id = 74342
        self.title = title
        self.blocks = []
        self.is_published = True
        self.subsite_id = subsite_id
        self.session = requests.Session()
        with open('.env', 'r') as env_file:
            self.session.headers = json.load(env_file)
            self.session.headers.update({"x-this-is-csrf": "THIS IS SPARTA!"})

    @staticmethod
    def gen_random_line(length=8, chars=string.ascii_letters + string.digits):
        return ''.join([choice(chars) for i in range(length)])

    # @staticmethod
    def upload_from_file(self, file_name: str):
        """
            Загрузить файл с диска, путь относительный
        """
        with open(file_name, 'rb') as i_f:
            response = self.session.post('https://api.dtf.ru/v1.8/uploader/upload', files={f'file_0': i_f}).json()
            return response['result'][0]

    # @staticmethod
    def alternative_upload_from_file(self, file_name: str, extension: str = '', file_type: str = ''):
        """
            - Загрузить файл с диска, путь относительный
            - extension ?= /audio
            - file_type ?= video/mp4
        """
        if self.session.headers.get('osnova-remember', False) and self.session.headers.get('osnova-remember') != 'replace_me':
            with open(file_name, 'rb') as i_f:
                response = self.session.post(f'https://dtf.ru/andropov/upload{extension}', files={f'file_0': (file_name, i_f, file_type)}).json()
                return response['result'][0]
        else:
            print('Add osnova-remember and osnova-session cookies to .env')
            return {}

    # @staticmethod
    def upload_from_folder(self, folder_name: str):
        """
            Загрузить все файлы из папки, путь относительный
        """
        upl_imgs = list()
        my_list = list()
        limit = 10
        for extension in ('*.jpeg', '*.jpg', '*.png'):
            my_list.extend(glob.iglob(f"{folder_name}/{extension}"))

        my_list_chunks = [my_list[i * limit:(i + 1) * limit] for i in range((len(my_list) + limit - 1) // limit)]

        for _, img_slice in enumerate(my_list_chunks):
            print(f'{_}/{len(my_list_chunks)}')
            images = self.session.post('https://api.dtf.ru/v1.8/uploader/upload', files={f'file_{i}': (self.gen_random_line(), open(x, 'rb')) for i, x in enumerate(img_slice)}).json()
            upl_imgs.extend(images['result'])

        return zip(map(lambda x: x.split('.')[0].split('\\')[-1], my_list), upl_imgs)

    @staticmethod
    def generate_block(block_type: str, block_data: dict, block_cover: bool, block_anchor: str, wrap: bool = False) -> dict:
        """
            Args:
                - block_type
                - block_data
                - block_cover
                - block_anchor
        """
        return {
            'type': block_type,
            'data': {block_type: block_data} if wrap else block_data,
            'cover': block_cover,
            'anchor': block_anchor
        }

    @staticmethod
    def generate_anchor_link(link_text: str, link_anchor: str) -> str:
        """
            Генерирует ссылку на якорь(anchor)
        """
        return f'''<a href="#{link_anchor}">{link_text}</a>'''

    @staticmethod
    def generate_qr_codes(items: list, save_path: str = 'qr'):
        for _, image in items:
            print(image['data']['uuid'])
            img = Image.new('L', (image['data']['width'], image['data']['height']), 255)
            url = pyqrcode.create(image['data']['uuid'], version=5)
            buffer = BytesIO()
            url.png(buffer, scale=6)
            with Image.open(buffer) as buffer_qr_img:
                img.paste(buffer_qr_img, (0, 0))
            img.save(f"{save_path}/{image['data']['uuid']}.png")

    def add_text_block(self, text: str = 'Пустой блок текста', cover: bool = False, anchor: str = ''):
        """
            :str: Текст блока

            :bool: Вывод в ленту

            :str: Якорь
        """
        self.blocks.append(
            self.generate_block('text', {'text': text}, cover, anchor)
        )

    def add_header_block(self, text: str = 'Заголовок', size: int = 2, cover: bool = False, anchor: str = ''):
        """
            :str: Текст заголовка

            :int: Размер заголовка 2-3-4

            :bool: Вывод в ленту

            :str: Якорь
        """
        style = f'h{max(min(size, 4), 2)}'
        self.blocks.append(
            self.generate_block('header', {'text': text, 'style': style}, cover, anchor)
        )

    def add_media_list(self, items: list):
        """
            Добавляет изображения как отдельные блоки, автоцентровка если высота > ширины

            :list: Список изображений
        """
        for file_name, item in items:
            width, height = sorted([item['data']['width'], item['data']['height']])
            if height % width > 100:
                back = not item['data']['width'] > item['data']['height']
            else:
                back = item['data']['width'] < 680 or item['data']['height'] > 1000
            self.add_media_block(item, background=back, anchor=file_name)

    def add_media_block(self, item: dict, title: str = '', author: str = '', background: bool = True, border: bool = False, cover: bool = False, anchor: str = ''):
        """
            :dict: Cловарь с данными загруженного изображения

            :str: Заметка к изображению

            :str: Автор изображения

            :bool: Отцентрировать изображение

            :bool: Добавить рамку

            :bool: Вывод в ленту

            :str: Якорь
        """
        self.blocks.append(
            self.generate_block('media', {'items': [{"title": title, "author": author, "image": item}], 'with_background': background, 'with_border': border}, cover, anchor)
        )

    def add_gallery_block(self, images: list, cover: bool = False, anchor: str = ''):
        self.blocks.append(
            self.generate_block('media', {'items': [{"title": '', "author": '', "image": image} for image in images], 'with_background': False, 'with_border': False}, cover, anchor)
        )

    def add_number_block(self, number: str = '', title: str = '', cover: bool = False, anchor: str = ''):
        """
            - :str: Число
            - :str: Описание числа
            - :bool: Вывод в ленту
            - :str: Якорь
        """
        self.blocks.append(
            self.generate_block('number', {"number": number, "title": title}, cover, anchor)
        )

    def add_quiz_block(self, items: list, title: str = '', is_public: bool = False, cover: bool = False, anchor: str = ''):
        self.blocks.append(
            self.generate_block('quiz', {"hash": '', "title": title, "new_items": items, "is_public": is_public, 'is_just_created': True}, cover, anchor)
        )

    def add_audio_block(self, audio_dict: dict, image_dict: dict = None, title: str = '', _hash: str = '', cover: bool = False, anchor: str = ''):
        self.blocks.append(
            self.generate_block('audio', {"title": title, "hash": _hash or self.gen_random_line(), "image": image_dict, "audio": audio_dict}, cover, anchor)
        )

    def add_delimiter_block(self, _type: str = 'default', cover: bool = False, anchor: str = ''):
        self.blocks.append(
            self.generate_block('delimiter', {"type": _type}, cover, anchor)
        )

    def add_code_block(self, text: str = '', lang: str = '', cover: bool = False, anchor: str = ''):
        self.blocks.append(
            self.generate_block('code', {"text": text, 'lang': lang}, cover, anchor)
        )

    def add_list_block(self, items: list, _type: str = 'UL', cover: bool = False, anchor: str = ''):
        self.blocks.append(
            self.generate_block('list', {"items": items, 'type': _type}, cover, anchor)
        )

    def add_warning_block(self, title: str, text: str, cover: bool = False, anchor: str = ''):
        """
            Нужно разрешение редакции на использование этого блока
        """
        self.blocks.append(
            self.generate_block('warning', {"title": title, "text": text}, cover, anchor)
        )

    def add_special_button(self, url: str, text: str = 'Перейти к посту', text_color: str = "#000000", background_color: str = "#d9f5ff", cover: bool = False, anchor: str = ''):
        """
            Нужно разрешение редакции на использование этого блока
        """
        self.blocks.append(
            self.generate_block('special_button', {"text": text, "textColor": text_color, "backgroundColor": background_color, "url": url}, cover, anchor)
        )

    def add_rawhtml_block(self, raw: str, cover: bool = False, anchor: str = ''):
        """
            Нужно разрешение редакции на использование этого блока
        """
        self.blocks.append(
            self.generate_block('rawhtml', {"raw": raw}, cover, anchor)
        )

    def add_quote_block(self, text: str, subline1: str = '', subline2: str = '', _type: str = 'default', size: str = 'small', image: dict = None, cover: bool = False, anchor: str = ''):
        """
            - subline1 = Имя
            - subline2 = Должность
            - type = default / opinion
            - size = small / big
        """
        self.blocks.append(
            self.generate_block('quote', {"text": text, "subline1": subline1, "subline2": subline2, "type": _type, "text_size": size, "image": image}, cover, anchor)
        )

    def add_incut_block(self, text: str, _type: str = 'centered', size: str = 'big', cover: bool = False, anchor: str = ''):
        """
            - text = not/formated text
            - type = left / centered
            - size = small / big
        """
        self.blocks.append(
            self.generate_block('incut', {"text": text, "type": _type, "text_size": size}, cover, anchor)
        )

    def extract_link(self, url: str, cover: bool = False, anchor: str = ''):
        response = self.session.get(f'https://dtf.ru/andropov/extract/render?url={url}').json()
        response_type = response['result'][0]['type']
        if response_type != 'error':
            print(response_type)
            if response_type == 'image':
                self.add_media_block(response['result'][0], cover=cover, anchor=anchor)
            elif response_type in ('link', 'video'):
                self.blocks.append(
                    self.generate_block(response_type, response['result'][0], cover, anchor, True)
                )
            else:
                print(f'Not implemented type {response_type}')
        else:
            print(f'Error extracting {url}')

    def publish_post(self):
        response = self.session.post('https://api.dtf.ru/v1.8/entry/create', data={
            "user_id": self.user_id,
            "title": self.title,
            "entry": json.dumps({
                "blocks":
                    self.blocks
            }),
            "is_published": self.is_published,
            "subsite_id": self.subsite_id
        })
        print(response.text)
