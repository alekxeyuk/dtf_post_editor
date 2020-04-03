from post_editor import Post
from helpers.markdown_helper import form_str
from helpers.telegraph_helper import parse_and_post_to_telegraph

if __name__ == "__main__":
    TEST_POST = Post('последний пост, я ухожу', subsite_id=132168) # 64969 132168 203796
    TEST_POST.add_media_block(TEST_POST.upload_from_file('621118.jpg'), 'Re: Zero', 'Felix', background=False, cover=True) # Картинка для вывода в ленту
    Post.generate_qr_codes(TEST_POST.upload_from_folder('source'), save_path='qr') # генерируем qr коды для изображений из папки source в папку qr
    TEST_POST.add_media_list(TEST_POST.upload_from_folder('qr'))
    link_to_telegraph = parse_and_post_to_telegraph(TEST_POST.title, TEST_POST.blocks, {'https':'socks4://109.202.17.4:61210'})
    TEST_POST.add_audio_block(TEST_POST.alternative_upload_from_file('OxT - GO CRY GO.mp3', '/audio'), title='OxT - GO CRY GO', cover=True)
    TEST_POST.extract_link(link_to_telegraph, True)
    TEST_POST.add_text_block(form_str('==AaA== ***bBb***'), True)
    TEST_POST.publish_post()
