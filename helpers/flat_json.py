# -*- coding: utf8 -*-
def flatten_json(json_dict: dict, block_i: int) -> dict:
    out = {}

    def flatten(x: dict, name: str = '') -> None:
        if isinstance(x, dict):
            for a in x:
                flatten(x[a], name + a + '~')
        elif isinstance(x, list):
            for i, a in enumerate(x):
                flatten(a, name + str(i) + '~')
        else:
            out[name[:-1]] = x

    flatten(json_dict)
    return {
        f"entry[entry][blocks][{block_i}][{key.replace('~', '][')}]": value for key, value in out.items()
    }
