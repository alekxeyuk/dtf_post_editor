import glob
import json
import string
from io import BytesIO
from random import choice

import pyqrcode
import requests
from PIL import Image

SESSION = requests.Session()
with open('.env', 'r') as env_file:
    SESSION.headers = json.load(env_file)
    SESSION.headers.update({"x-this-is-csrf": "THIS IS SPARTA!"})

def gen_random_line(length=8, chars=string.ascii_letters + string.digits):
    return ''.join([choice(chars) for i in range(length)])

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

    @staticmethod
    def upload_from_file(file_name: str):
        """
            Загрузить файл с диска, путь относительный
        """
        with open(file_name, 'rb') as i_f:
            response = SESSION.post('https://api.dtf.ru/v1.8/uploader/upload', files={f'file_0': i_f}).json()
            return response['result'][0]

    @staticmethod
    def alternative_upload_from_file(file_name: str, extension: str = ''):
        """
            Загрузить файл с диска, путь относительный
        """
        if SESSION.headers.get('osnova-remember', False) and SESSION.headers.get('osnova-session', False):
            with open(file_name, 'rb') as i_f:
                response = SESSION.post(f'https://dtf.ru/andropov/upload{extension}', files={f'file_0': i_f}).json()
                return response['result'][0]
        else:
            print('Add osnova-remember and osnova-session cookies to .env')

    @staticmethod
    def upload_from_folder(folder_name: str):
        """
            Загрузить все файлы из папки, путь относительный
        """
        upl_imgs = list()
        my_list = list()
        n = 10
        for extension in ('*.jpeg', '*.jpg', '*.png'):
            my_list.extend(glob.iglob(f"{folder_name}/{extension}"))

        my_list_chunks = [my_list[i * n:(i + 1) * n] for i in range((len(my_list) + n - 1) // n)]

        for _, img_slice in enumerate(my_list_chunks):
            print(f'{_}/{len(my_list_chunks)}')
            images = SESSION.post('https://api.dtf.ru/v1.8/uploader/upload', files={f'file_{i}': open(x, 'rb') for i, x in enumerate(img_slice)}).json()
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
            n, m = sorted([item['data']['width'], item['data']['height']])
            if m % n > 100:
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
            self.generate_block('audio', {"title": title, "hash": _hash or gen_random_line(), "image": image_dict, "audio": audio_dict}, cover, anchor)
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

    def add_rawhtml_button(self, raw: str, cover: bool = False, anchor: str = ''):
        """
            Нужно разрешение редакции на использование этого блока
        """
        self.blocks.append(
            self.generate_block('rawhtml', {"raw": raw}, cover, anchor)
        )

    def extract_link(self, url: str, cover: bool = False, anchor: str = ''):
        response = SESSION.get(f'https://dtf.ru/andropov/extract/render?url={url}').json()
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
        response = SESSION.post('https://api.dtf.ru/v1.8/entry/create', data={
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


if __name__ == "__main__":
    TEST_POST = Post('Ломаем верстку', subsite_id=132168) # 64969 132168 203796
    # TEST_POST.add_quiz_block(['Игорь', 'Простагма'], title='ГОЛОСУЕМ?', is_public=True, cover=True)
    # TEST_POST.add_warning_block('Test', 'test', True)
    TEST_POST.add_text_block("""<mark class="block-warning">
    Test
    </mark>""", True)
    TEST_POST.add_header_block(f"""
    <span class="block-warning__title thesis__submit ui-button ui-button--1">Внимание</span>
    <span class="block-warning thesis__submit ui-button ui-button--1">{'h'*10000000}</span>
    <h1 class="block-warning thesis__submit ui-button ui-button--1">В тексте нет сюжетных спойлеров, но описана завязка и то, как работает геймплей на протяжении всей кампании. Если вы всё равно опасаетесь, долистайте до самого конца, где описываются общие впечатления.</h1>
    """, True)
    TEST_POST.add_text_block("""<h1 class="block-warning thesis__submit ui-button ui-button--1">В тексте нет сюжетных спойлеров, но описана завязка и то, как работает геймплей на протяжении всей кампании. Если вы всё равно опасаетесь, долистайте до самого конца, где описываются общие впечатления.</h1>""", True)
    TEST_POST.add_text_block("""<span class="thesis__submit ui-button ui-button--1">Внимание</span>""", True)
    TEST_POST.add_text_block("""<button class="thesis__submit ui-button ui-button--1">Внимание</button>""", True)
    TEST_POST.add_text_block("""<a class="thesis__submit ui-button ui-button--1" href="/writing?to=new">Ссылка на новую запись</a>""", True)
    TEST_POST.add_text_block("""<a class="main_menu__write-button ui-button ui-button--12 ui-button--small lm-hidden l-mr-5">Внимание</a>""", True)
    TEST_POST.add_text_block("""<span class="main_menu__write-button ui-button ui-button--12 ui-button--small lm-hidden l-mr-5">Внимание</span>""", True)
    TEST_POST.add_text_block("""<span class="block-warning" style="font-size: 306px;">Внимание</span>""", True)
    TEST_POST.add_text_block("""<span class="hljs-keyword">Внимание</span>""", True)
    TEST_POST.publish_post()
    exit()
    # TEST_POST.extract_link('https://docs.python.org/3/_static/py.png', True)
    # TEST_POST.extract_link('https://docs.python.org/3/tutorial/index.html', True)
    # TEST_POST.extract_link('https://youtu.be/y6DbaBNyJzE', True)
    # TEST_POST.extract_link('https://media.giphy.com/media/xULW8OofuT5CAhTVWU/giphy.gif', True)
    # TEST_POST.extract_link('https://www.verdict.co.uk/wp-content/uploads/2017/09/giphy-downsized-large.gif', True)
    # TEST_POST.extract_link('https://leonardo.osnova.io/744f8fcb-2542-bf14-dd17-91eff63950a1/', True)
    # TEST_POST.add_number_block('400', 'рублей', True)
    # TEST_POST.add_quiz_block(['Норм', 'Плохо'], title='Как дела?', is_public=True, cover=True)
    # TEST_POST.add_audio_block(Post.alternative_upload_from_file('OxT - GO CRY GO.mp3', '/audio'), Post.upload_from_file('cover.jpg'), 'OxT - GO CRY GO')
    # TEST_POST.add_delimiter_block(cover=True)
    # TEST_POST.add_code_block('std::cout << "test";')
    # TEST_POST.add_list_block([1, 2, 3, 4, 5], 'UL')
    # TEST_POST.add_text_block('***text*** **text** *block* ==text== [text](http://ya.ru)', True)
    TEST_POST.publish_post()
    exit()
    a = """Рэм,qr/rem
        Рам,qr/ram
        Рам и Рэм,qr/RamRem
        Анастасия Хошин,qr/Anastasia
        Беатрис,qr/beatrice
        Терезия ван Астрея,qr/Thearesia
        Круш Карштен,qr/crush
        Эльза Гранхирт,qr/Elsa
        Эмилия,qr/emilia
        Феликс Аргайл,qr/felix
        Фелт,qr/Felt
        Пёрлбатон,qr/Hetaro
        Юлий Юклий,qr/Julius
        Присцилла Бариэль,qr/Priscilla
        Райнхард ван Астрея,qr/Reinhard
        Росвелл Л. Матерс,qr/rozvall
        Групповуха,qr/combo
        Рандом,qr/random"""
    test_post = Post(title='Re: Zero Infinity', subsite_id=132168) # Инициализация поста с названием и ID подсайта
    test_post.add_media_block(Post.upload_from_file('cover.jpg'), 'Re: Zero Infinity', 'QooApp', background=False, cover=True) # Картинка для вывода в ленту
    test_post.add_text_block('Наслаждаемся артами из игры по Re: Zero 🔥', cover=True) # Просто текст
    test_post.add_header_block(Post.generate_anchor_link('Комментарии', 'qrfast'), cover=False) # Заголовок 2 размера, с ссылкой на якорь
    #Post.generate_qr_codes(Post.upload_from_folder('source'), save_path='qr') # генерируем qr коды для изображений из папки source в папку qr
    a = dict(map(lambda x: x.strip().split(','), a.split('\n')))
    for h_name, f_upl in a.items():
        test_post.add_header_block(Post.generate_anchor_link(h_name, f_upl.replace('/', '')))
    for h_name, f_upl in a.items():
        test_post.add_header_block(h_name, anchor=f_upl.replace('/', ''))
        test_post.add_media_list(Post.upload_from_folder(f_upl))
    test_post.add_text_block('Спасибо за внимание, данный пост создан в моем post_editor v0.2a') # Просто текст
    test_post.add_text_block('#qrfast', anchor='qrfast') # хэштег с якорем
    test_post.publish_post()
