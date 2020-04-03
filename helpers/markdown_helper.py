import re

regex = r"\*\*(?P<bold>\S+)\*\*|\*(?P<italic>\S+)\*|==(?P<wrap>\S+)==|\[(?P<url>\S+\]\(\S+)\)"

p = re.compile(regex, re.MULTILINE)

func_dict = {
    'wrap': lambda x: (f"<mark>{x}</mark>", f"=={x}=="),
    'bold': lambda x: (f"<b>{x}</b>", f"**{x}**"),
    'italic': lambda x: (f"<i>{x}</i>", f"*{x}*"),
    'url': lambda x: ("<a href='{1}' target='_blank'>{0}</a>".format(*x.split('](')), f"[{x})"),
}

def format_string(test_str: str) -> str:
    matches = list(p.finditer(test_str))
    for match in matches:
        for key, item in match.groupdict().items():
            if item:
                x, y = func_dict[key](item)
                return format_string(test_str.replace(y, x))
    return test_str

def form_str(string: str) -> str:
    """
    Форматирование строки по markdown
        - Строка с тегами разделенными пробелами
        - Теги можно комбинировать
        - italic
        - bold
        - marker wrap
        - a tag
    """
    return ' '.join(map(format_string, string.split(' ')))
