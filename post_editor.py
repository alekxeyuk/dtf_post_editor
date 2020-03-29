import glob
import json
from io import BytesIO

import pyqrcode
import requests
from PIL import Image

SESSION = requests.Session()
with open('.env', 'r') as env_file:
    SESSION.headers = json.load(env_file)

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
            responce = SESSION.post('https://api.dtf.ru/v1.8/uploader/upload', files={f'file_0': i_f}).json()
            return responce['result'][0]

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
    def generate_block(block_type: str, block_data: dict, block_cover: bool, block_anchor: str) -> dict:
        return {
            'type': block_type,
            'data': block_data,
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
    test_post = Post(title='Просто тест #42', subsite_id=132168) # Инициализация поста с названием и ID подсайта
    test_post.add_media_block(Post.upload_from_file('anime.png'), 'Добро пожаловать', 'Аниме', background=False, cover=True) # Картинка для вывода в ленту
    test_post.add_text_block('Тестовый пост написанный в моем редакторе 🔥', cover=True) # Просто текст
    test_post.add_header_block(Post.generate_anchor_link('Заголовок-ссылка', 'qrfast'), cover=False) # Заголовок 2 размера, с ссылкой на якорь
    #Post.generate_qr_codes(Post.upload_from_folder('source'), save_path='qr') # генерируем qr коды для изображений из папки source в папку qr
    test_post.add_media_list(Post.upload_from_folder('qr')) # загружаем и добавляем изображения из папки qr
    test_post.add_text_block('Спасибо за внимание, данный пост создан в моем post_editor v0.1a') # Просто текст
    test_post.add_text_block('#qrfast', anchor='qrfast') # хэштег с якорем
    test_post.publish_post()
