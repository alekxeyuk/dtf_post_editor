import json
import string
import time
from pathlib import Path
from random import choice
from webbrowser import open_new_tab

import qrcode
import requests
from PIL import Image, ImageDraw
from bs4 import BeautifulSoup
try:
    from .helpers.flat_json import flatten_json
except ImportError:
    from helpers.flat_json import flatten_json


class Post:
    """
        Класс для создания поста на DTF

        __init__:

        :str: Название поста, можно оставить пустым

        :int: ID подсайта для публикации
    """
    def __init__(self, title: str = '', subsite_id: int = 132168, cookies_file: str = '.env', cookies_dict: dict = None, api_v: str = '1.9'):
        self.user_id = 0
        self.post_id = 0
        self.title = title
        self.blocks = []
        self.is_published = True
        self.subsite_id = subsite_id

        self.api_v = api_v
        self.session = requests.Session()
        if cookies_dict:
            self.update_cookies_from_dict(cookies_dict)
        else:
            self.update_cookies_from_file(cookies_file)
        self.logged_in = self.check_auth()

    def check_auth(self):
        response = self.session.get("https://dtf.ru/auth/check?mode=raw", data={"mode": "raw"}).json()
        if response['rc'] == 200:
            self.user_id = response['data']['id']
            self.user_name = response['data']['name']
            return True
        return False

    def update_cookies_from_dict(self, cookies_dict: dict):
        self.session.headers.update(cookies_dict)
        self.session.headers.update({"x-this-is-csrf": "THIS IS SPARTA!"})
        self.session.cookies.update(self.session.headers)

    def update_cookies_from_file(self, file_name: str):
        with open(file_name, 'r') as env_file:
            self.session.headers = json.load(env_file)
            self.session.headers.update({"x-this-is-csrf": "THIS IS SPARTA!"})
            self.session.cookies.update(self.session.headers)

    @staticmethod
    def gen_random_line(length=8, chars=string.ascii_letters + string.digits):
        return ''.join([choice(chars) for i in range(length)])

    def upload_from_file(self, file_name: str):
        """
            Загрузить файл с диска, путь относительный
        """
        with open(file_name, 'rb') as i_f:
            response = self.session.post(f'https://api.dtf.ru/v{self.api_v}/uploader/upload', files={f'file_0': i_f}).json()
            return response['result'][0]

    def alternative_upload_from_file(self, file_name: str, extension: str = '', file_type: str = ''):
        """
            - Загрузить файл с диска, путь относительный
            - extension ?= /audio
            - file_type ?= video/mp4
        """
        if self.session.headers.get('osnova-remember', False) and self.session.headers.get('osnova-remember') != 'replace_me':
            with open(file_name, 'rb') as i_f:
                if not(extension or file_type):
                    if file_name.endswith('mp4'):
                        file_type = 'video/mp4'
                    elif file_name.endswith('mp3'):
                        extension = '/audio'
                response = self.session.post(f'https://dtf.ru/andropov/upload{extension}', files={f'file_0': (file_name.split('\\')[-1], i_f, file_type)}).json()
                return response['result'][0]
        else:
            print('Add osnova-remember and osnova-session cookies to .env')
            return {}

    def upload_from_folder(self, folder_path: str, recursive: bool = False):
        """
            - Загрузить все файлы из папки, путь относительный/абсолютный
            - Возможно загрузить все файлы рекурсивно
        """
        upl_imgs = list()
        my_list = list()
        limit = 10
        for extension in ('*.jfif', '*.jpeg', '*.jpg', '*.png', '*.webp'):
            if recursive:
                my_list.extend(Path(folder_path).rglob(extension))
            else:
                my_list.extend(Path(folder_path).glob(extension))

        my_list_chunks = [my_list[i * limit:(i + 1) * limit] for i in range((len(my_list) + limit - 1) // limit)]

        for _, img_slice in enumerate(my_list_chunks):
            print(f'{_}/{len(my_list_chunks)}')
            images = self.session.post(f'https://api.dtf.ru/v{self.api_v}/uploader/upload', files={f'file_{i}': (self.gen_random_line(), open(x, 'rb')) for i, x in enumerate(img_slice)}).json()
            upl_imgs.extend(images['result'])

        return zip(map(lambda x: x.name.split('.')[0], my_list), upl_imgs)

    @staticmethod
    def generate_block(block_type: str, block_data: dict, block_cover: bool, block_anchor: str, wrap: bool = False, DBLwrap: bool = False, **kwargs) -> dict:
        """
            Args:
                - block_type
                - block_data
                - block_cover
                - block_anchor
                - wrap
                - DBLwrap
                - hidden
        """
        data = block_data
        if wrap:
            data = {block_type: block_data}
        elif DBLwrap:
            data = {block_type: {'type': block_type, 'data': block_data}}
        return {
            'type': block_type,
            'data': data,
            'cover': block_cover,
            'anchor': block_anchor
        } | kwargs

    @staticmethod
    def generate_link(link_text: str, link_url: str) -> str:
        """
            Генерирует ссылку
        """
        return f'''<a href="{link_url}">{link_text}</a>'''

    def generate_qr_codes(self, items: list, save_path: str = 'qr', save_to_db: bool = True, keep_file_name: bool = False):
        for _, image in items:
            if image['data'].get('uuid', None) is None:
                print(image)
                continue
            print(image['data']['uuid'])
            background = Image.new('RGBA', (image['data']['width'], image['data']['height']), (0, 0, 0, 0))
            qr = qrcode.QRCode(
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=8,
                border=2,
            )
            qr.add_data(image['data']['uuid'])
            qr.make(fit=True)
            qr_img = qr.make_image(fill_color="black", back_color="white")
            background.paste(qr_img, (0, 0))
            ImageDraw.Draw(background).text((4, 0), 'prostagma? qr-nsfw v2', (0, 0, 0))
            file_name = image['data']['uuid'] if not keep_file_name else _
            background.save(f"{save_path}/{file_name}-png.png")
            if save_to_db:
                qr_image = self.upload_from_file(f"{save_path}/{file_name}-png.png")
                print(self.session.post("https://python-flask.alekxuk.now.sh/v1/qrcodes/insert", json={
                    'uuid': image['data']['uuid'],
                    'qr_uuid': qr_image['data']['uuid'],
                    'qr_data': f"{image['data']['uuid']}|{image.get('data').get('type')}",
                    'entry_data': {'type': image.get('type'), 'file_type': image.get('data').get('type')}
                }).json())

    def add_text_block(self, text: str = 'Пустой блок текста', cover: bool = False, anchor: str = '', **kwargs):
        """
            :str: Текст блока

            :bool: Вывод в ленту

            :str: Якорь
        """
        self.blocks.append(
            self.generate_block('text', {'text': text}, cover, anchor, **kwargs)
        )

    def add_header_block(self, text: str = 'Заголовок', size: int = 2, cover: bool = False, anchor: str = '', **kwargs):
        """
            :str: Текст заголовка

            :int: Размер заголовка 2-3-4

            :bool: Вывод в ленту

            :str: Якорь
        """
        style = f'h{max(min(size, 4), 2)}'
        self.blocks.append(
            self.generate_block('header', {'text': text, 'style': style}, cover, anchor, **kwargs)
        )

    def add_media_list(self, items: list, cover_count: int = 0, auto_back: bool = True, imp_back: bool = False, add_anchor: bool = True):
        """
        Добавляет изображения как отдельные блоки, автоцентровка если высота > ширины
            - :list: Список изображений
            - :int:  Количество блоков для вывода в ленту
            - :bool: Автоцентровка
            - :bool: Принудительное не/центрирование
        """
        counter = 0
        for file_name, item in items:
            if item.get('type') == 'error':
                print(file_name, 'broken image')
                continue
            if auto_back:
                width, height = sorted([item['data']['width'], item['data']['height']])
                if height % width > 100:
                    imp_back = not item['data']['width'] > item['data']['height']
                else:
                    imp_back = item['data']['width'] < 680 or item['data']['height'] > 1000
            self.add_media_block(item, background=imp_back, anchor=file_name * add_anchor, cover=counter < cover_count)
            counter += 1


    def add_media_block(self, item: dict, title: str = '', author: str = '', background: bool = True, border: bool = False, cover: bool = False, anchor: str = '', **kwargs):
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
            self.generate_block('media', {'items': [{"title": title, "author": author, "image": item}], 'with_background': background, 'with_border': border}, cover, anchor, **kwargs)
        )

    def add_gallery_block(self, images: list, cover: bool = False, anchor: str = '', **kwargs):
        self.blocks.append(
            self.generate_block('media', {'items': [{"title": '', "author": '', "image": image[1] if isinstance(image, tuple) else image} for image in images], 'with_background': False, 'with_border': False}, cover, anchor, **kwargs)
        )

    def add_number_block(self, number: str = '', title: str = '', cover: bool = False, anchor: str = '', **kwargs):
        """
            - :str: Число
            - :str: Описание числа
            - :bool: Вывод в ленту
            - :str: Якорь
        """
        self.blocks.append(
            self.generate_block('number', {"number": number, "title": title}, cover, anchor, **kwargs)
        )

    def add_quiz_block(self, items: list, title: str = '', is_public: bool = False, cover: bool = False, anchor: str = '', **kwargs):
        """
        - Варианты ответа
        - Название
        - Публичность опроса
        """
        self.blocks.append(
            self.generate_block('quiz', {"uid": self.gen_random_line(29), "hash": self.gen_random_line(16), "title": title, "items": {f'a{int(time.time())}{x}': item for x, item in enumerate(items)}, "is_public": is_public, 'is_just_created': True}, cover, anchor, **kwargs)
        )

    def add_audio_block(self, audio_dict: dict, image_dict: dict = {}, title: str = '', _hash: str = '', cover: bool = False, anchor: str = '', **kwargs):
        self.blocks.append(
            self.generate_block('audio', {"title": title, "hash": _hash or self.gen_random_line(), "image": image_dict, "audio": audio_dict}, cover, anchor, **kwargs)
        )

    def add_delimiter_block(self, _type: str = 'default', cover: bool = False, anchor: str = '', **kwargs):
        self.blocks.append(
            self.generate_block('delimiter', {"type": _type}, cover, anchor, **kwargs)
        )

    def add_code_block(self, text: str = '', lang: str = '', cover: bool = False, anchor: str = '', **kwargs):
        self.blocks.append(
            self.generate_block('code', {"text": text, 'lang': lang}, cover, anchor, **kwargs)
        )

    def add_list_block(self, items: list, _type: str = 'UL', cover: bool = False, anchor: str = '', **kwargs):
        self.blocks.append(
            self.generate_block('list', {"items": items, 'type': _type}, cover, anchor, **kwargs)
        )

    def add_warning_block(self, title: str, text: str, cover: bool = False, anchor: str = '', **kwargs):
        """
            Нужно разрешение редакции на использование этого блока
        """
        self.blocks.append(
            self.generate_block('warning', {"title": title, "text": text}, cover, anchor, **kwargs)
        )

    def add_special_button(self, url: str, text: str = 'Перейти к посту', text_color: str = "#000000", background_color: str = "#d9f5ff", cover: bool = False, anchor: str = '', **kwargs):
        """
            Нужно разрешение редакции на использование этого блока
        """
        self.blocks.append(
            self.generate_block('special_button', {"text": text, "textColor": text_color, "backgroundColor": background_color, "url": url}, cover, anchor, **kwargs)
        )

    def add_rawhtml_block(self, raw: str, cover: bool = False, anchor: str = '', **kwargs):
        """
            Нужно разрешение редакции на использование этого блока
        """
        self.blocks.append(
            self.generate_block('rawhtml', {"raw": raw}, cover, anchor, **kwargs)
        )

    def add_wtrfall_block(self, wtrfallid: str, cover: bool = False, anchor: str = '', **kwargs):
        """
            Нужно разрешение редакции на использование этого блока
        """
        self.blocks.append( 
            self.generate_block('wtrfall', {"wtrfallid": wtrfallid}, cover, anchor, **kwargs)
        )

    def add_quote_block(self, text: str, subline1: str = '', subline2: str = '', _type: str = 'default', size: str = 'small', image: dict = None, cover: bool = False, anchor: str = '', **kwargs):
        """
            - subline1 = Имя
            - subline2 = Должность
            - type = default / opinion
            - size = small / big
        """
        self.blocks.append(
            self.generate_block('quote', {"text": text, "subline1": subline1, "subline2": subline2, "type": _type, "text_size": size, "image": image}, cover, anchor, **kwargs)
        )

    def add_incut_block(self, text: str, _type: str = 'centered', size: str = 'big', cover: bool = False, anchor: str = '', **kwargs):
        """
            - text = not/formated text
            - type = left / centered
            - size = small / big
        """
        self.blocks.append(
            self.generate_block('incut', {"text": text, "type": _type, "text_size": size}, cover, anchor, **kwargs)
        )

    def add_person_block(self, image: dict = None, title: str = '', description: str = '', cover: bool = False, anchor: str = '', **kwargs):
        self.blocks.append(
            self.generate_block('person', {'image': image, 'title': title, 'description': description}, cover, anchor, **kwargs)
        )
        
    def add_embed_block(self, original_id: int, cover: bool = False, anchor: str = '', **kwargs):
        self.blocks.append(
            self.generate_block('osnovaEmbed', {'original_id': original_id}, cover, anchor, DBLwrap = True, **kwargs)
        )

    def extract_link(self, url: str, cover: bool = False, anchor: str = ''):
        response = self.session.get(f'https://dtf.ru/andropov/extract?url={url}').json()
        response_type = response['result'][0]['type']
        if response_type != 'error':
            print(response_type)
            if response_type == 'image':
                self.add_media_block(response['result'][0], cover=cover, anchor=anchor)
            elif response_type in ('link', 'video'):
                self.blocks.append(
                    self.generate_block(response_type, response['result'][0], cover, anchor, True)
                )
            elif response_type == 'universalbox':
                box_service = response['result'][0]['data']['service']
                self.blocks.append(
                    self.generate_block(box_service, response['result'][0], cover, anchor, True)
                )
            else:
                print(f'Not implemented type {response_type}')
        else:
            print(f'Error extracting {url}')

    def choose_draft(self, first: bool = False) -> int:
        """
        Выбор одного из 12 последних черновиков
        """
        drafts = dict()
        drafts_json = self.session.get(f'https://dtf.ru/u/{self.user_id}/drafts/more?last_id=1&mode=raw').json()
        bs = BeautifulSoup(drafts_json['data']['items_html'], 'lxml')
        for x, i in enumerate(bs.find_all(attrs={'class': 'feed__item l-island-round'}), start=1):
            post_id = i.div.get('data-content-id')
            post_to = i.find(attrs={'class': 'content-header-author__name'}).text.strip()
            if post_to == self.user_name:
                post_to = 'В блог'
            post_title = i.find(attrs={'class': 'content-title content-title--short l-island-a'})
            if post_title:
                post_title = post_title.text.strip()
            else:
                post_title = 'Без заголовка'
            print(f"[{x}]", post_id, ',', post_to, ',', post_title)
            drafts.update({x: dict(post_id=post_id, post_to=post_to, post_title=post_title)})
        if first:
            return drafts.get(1).get('post_id')
        else:
            while post_choice := input('Choose one of the drafts, enter to exit :> '):
                if post_choice.isdigit() and (post_choice := int(post_choice)) in range(1, 13):
                    return drafts.get(post_choice).get('post_id')


    def load_draft(self, draft_id: int, only_blocks: bool = True):
        """
        Загрузить структуру уже существующего черновика
        
        1. draft_id:
            - -1 -> последний черновик
            - 0  -> выбор из последних черновиков
        """
        if draft_id in (-1, 0):
            draft_id = self.choose_draft(bool(draft_id))

        editorData = self.session.get(f'https://dtf.ru/writing/{draft_id}/editorData?mode=raw').json()
        if editorData['rc'] != 200:
            print(editorData)
        else:
            entry = editorData['data']['entry']
            if not only_blocks:
                self.post_id = entry['id']
                self.title = entry['title']
                self.subsite_id = entry['subsite_id']
            self.blocks.extend(entry['entry']['blocks'])
            print('post extended with', len(entry['entry']['blocks']), 'blocks')


    def fix_block(self, block: dict) -> dict:
        if block['type'] == 'audio':
            if block['data']['image'] == None:
                block['data']['image'] = dict()
        return block

    def save_draft(self, debug: bool = False):
        """
        Создает новый черновик
        """
        if self.session.cookies.get('osnova-remember', None):
            draft_data = {
                "entry": json.dumps({
                    "id": self.post_id,
                    "title": self.title,
                    "subsite_id": self.subsite_id,
                    "is_published": False,
                    "entry": {
                        "blocks": self.blocks
                    }
                }),
                "mode": "raw"
            }
            response = self.session.post('https://dtf.ru/writing/save', data=draft_data)
        else:
            response = dict(text='No osnova-remember cookie in .env file')
        try:
            open_new_tab(response.json().get('data', {}).get('entry', {}).get('url', ''))
        except json.decoder.JSONDecodeError:
            print('Ошиб очка')
        print(response.text if debug else 'OK')

    def publish_post(self, ret: bool = False):
        response = self.session.post(f'https://api.dtf.ru/v{self.api_v}/entry/create', data={
            "user_id": self.user_id,
            "title": self.title,
            "entry": json.dumps({
                "blocks":
                    self.blocks
            }),
            "is_published": self.is_published,
            "subsite_id": self.subsite_id
        })
        if ret:
            return response.json()
        else:
            print(response.text)
