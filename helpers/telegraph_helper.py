from telegraph import Telegraph
from retry_decorator import retry

def block_create(uuid: str) -> dict:
    return {'attrs': {
                'src': f'https://leonardo.osnova.io/{uuid}/'
        }, 'tag': 'img'}

def parse_dtf_blocks(blocks: list) -> list:
    parsed_blocks = []
    for block in blocks:
        if block['type'] == 'media':
            if block['anchor']:
                parsed_blocks.append(block_create(block['anchor'].replace('-png', '').replace('-mp4', '')))
            else:
                for item in block['data']['items']:
                    image = item.get('image', None)
                    if image:
                        if isinstance(image, tuple):
                            image = image[1]
                        parsed_blocks.append(block_create(image['data']['uuid']))
    return parsed_blocks

@retry(Exception, tries=5, timeout_secs=0.1)
def parse_and_post_to_telegraph(title: str, blocks: list, proxies: dict = None) -> str:
    telegraph = Telegraph()
    if proxies:
        telegraph._telegraph.session.proxies = proxies
    telegraph.create_account(short_name='1337')
    content = parse_dtf_blocks(blocks)
    response = telegraph.create_page(
        title=title,
        content=content
    )
    return f'https://telegra.ph/{response["path"]}'
