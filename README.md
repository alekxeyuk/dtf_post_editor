# dtf_post_editor
 Easy image based post editor for dtf.ru/vc/tj
 
 [![Run on Repl.it](https://repl.it/badge/github/alekxeyuk/dtf_post_editor)](https://repl.it/github/alekxeyuk/dtf_post_editor)

 [![Gitpod Ready-to-Code](https://img.shields.io/badge/Gitpod-Ready--to--Code-blue?logo=gitpod)](https://gitpod.io/#https://github.com/alekxeyuk/dtf_post_editor) 

## Dependencies
- `Python 3.7` or higher
- `requests` [requests](https://github.com/kennethreitz/requests)
- `pillow` [pillow](https://github.com/python-pillow/Pillow)
- `pyqrcode` [pyqrcode](https://github.com/mnooner256/pyqrcode)

## Install
- Clone repository
- Install dependencies
```bash
pip install -r requirements.txt
```
- Rename `.env_mock` to `.env` and place your token inside
- Place your images in folder source/qr/anyothername
- Edit __init__ function to your likings 
- Then:
```bash
python post_editor.py
```

## License
[MIT](https://github.com/alekxeyuk/dtf_post_editor/blob/master/LICENSE)
