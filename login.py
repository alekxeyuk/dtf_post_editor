import requests
import json

def login():
    email, password = input('email:'), input('password:')
    r = requests.post("https://dtf.ru/auth/simple/login", data={"values[login]": email, "values[password]": password, "mode": "raw"}, headers={"x-this-is-csrf": "THIS IS SPARTA!"})
    r_json = r.json()
    print(r_json)
    if r_json.get('rc', 400) == 200:
        print(r.cookies.get_dict().get('osnova-remember'))
        env_j = None
        with open('.env', 'r') as f:
            try:
                env_j = json.load(f)
            except json.decoder.JSONDecodeError:
                env_j = dict()
            env_j.update({'osnova-remember': r.cookies.get_dict().get('osnova-remember')})
        with open('.env', 'w') as f:
            f.write(json.dumps(env_j))

if __name__ == "__main__":
    login()