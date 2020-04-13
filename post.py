from post_editor import Post
from helpers.markdown_helper import form_str
from helpers.telegraph_helper import parse_and_post_to_telegraph

if __name__ == "__main__":
    TEST_POST = Post('Все Тэги', subsite_id=132168) # 64969 132168 203796
    TEST_POST.add_text_block("text block text text")
    TEST_POST.add_text_block(form_str("**test** *test* ==Hello== [Test](http://ya.ru)"))

    TEST_POST.add_header_block('Заголовок Обычный', 4)
    TEST_POST.add_header_block(Post.generate_link('Заголовок Ссылка', '#qrfast'), 4)
    TEST_POST.add_header_block(form_str("**Заголовок** *МаркДаун* ==Hello== [Test](http://ya.ru)"), 2)

    TEST_POST.add_media_block(TEST_POST.upload_from_file('anime.png'), 'Название', 'Автор', False, False, True)
    TEST_POST.add_gallery_block(TEST_POST.upload_from_folder('source'))
    Post.generate_qr_codes(TEST_POST.upload_from_folder('source'), save_path='qr')
    TEST_POST.add_media_list(TEST_POST.upload_from_folder('qr'))

    TEST_POST.add_media_block(TEST_POST.alternative_upload_from_file('videoplayback.mp4', file_type="video/mp4"))

    TEST_POST.extract_link("https://docs.python.org/3/tutorial/index.html")
    TEST_POST.extract_link("https://youtu.be/1Jwo5qc78QU")

    TEST_POST.add_incut_block('Test<br>Incut', 'centered', 'big')
    TEST_POST.add_incut_block('Test<br>Incut', 'left', 'small')

    TEST_POST.add_quote_block('Da da ya', 'Имя', 'Должность', 'default', 'small', TEST_POST.upload_from_file('cover.jpg'))
    TEST_POST.add_quote_block('Da da ya', 'Имя', 'Должность', 'opinion', 'big', TEST_POST.upload_from_file('cover.jpg'))

    TEST_POST.add_list_block([1, 2, 3, 4, 5, 6], 'UL')
    TEST_POST.add_list_block(['a', 'b', 'c', 'd'], 'OL')

    TEST_POST.add_code_block('import time\ntime.sleep(1000)')

    TEST_POST.add_delimiter_block()

    TEST_POST.add_audio_block(TEST_POST.alternative_upload_from_file('OxT - GO CRY GO.mp3', '/audio'), title='OxT - GO CRY GO')
    TEST_POST.add_audio_block(TEST_POST.alternative_upload_from_file('OxT - GO CRY GO.mp3', '/audio'), title='OxT - GO CRY GO', image_dict=TEST_POST.upload_from_file('anime.png'))

    TEST_POST.add_quiz_block(['ДА', 'НЕТ'], 'Вам интересно?', is_public=True)

    TEST_POST.add_number_block('1000', 'часов потрачено')

    TEST_POST.add_text_block(Post.gen_random_line())

    link_to_telegraph = parse_and_post_to_telegraph(TEST_POST.title, TEST_POST.blocks, {'https':'socks4://109.202.17.4:61210'})
    TEST_POST.extract_link(link_to_telegraph, True)

    TEST_POST.add_text_block('#qrfast', anchor='qrfast')

    TEST_POST.publish_post()
