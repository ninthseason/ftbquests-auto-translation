import re
import nbtlib
import requests
import random
import json
from hashlib import md5


def str_preprocess(string: str):
    """为了尽量不破坏格式，在输入翻译模型前采用启发式的方法对字符串预处理"""
    """事实上还是存在bug"""
    format_str = re.findall("(?<!\\\\)&.", string)
    if '&&' in format_str:
        format_str.remove('&&')
    for i in format_str:
        string = string.replace(i, i + " ")
    string = string.strip()
    return string


class RelaxedParser(nbtlib.Parser):
    def collect_tokens_until(self, token_type):
        while True:
            try:
                yield from super().collect_tokens_until(token_type)
                return
            except nbtlib.InvalidLiteral as exc:
                if exc.args[1].startswith("Expected comma"):
                    yield self.current_token


class BaiduTranslateClient:
    def __init__(self, appid, appkey, from_lang="en", to_lang="zh"):
        self.appid = appid
        self.appkey = appkey
        self.from_lang = from_lang
        self.to_lang = to_lang

        endpoint = 'http://api.fanyi.baidu.com'
        path = '/api/trans/vip/translate'
        self.url = endpoint + path

    @staticmethod
    def make_md5(s, encoding='utf-8'):
        return md5(s.encode(encoding)).hexdigest()

    def callapi(self, text: str):
        """
        return like:
                {
                    "from": "en",
                    "to": "zh",
                    "trans_result": [
                        {
                            "src": "Hello World! This is 1st paragraph.",
                            "dst": "你好，世界！这是第一段。"
                        },
                        {
                            "src": "This is 2nd paragraph.",
                            "dst": "这是第2段。"
                        }
                    ]
                }"""
        query = text
        salt = random.randint(32768, 65536)
        sign = self.make_md5(self.appid + query + str(salt) + self.appkey)

        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        payload = {'appid': self.appid, 'q': query, 'from': self.from_lang, 'to': self.to_lang, 'salt': salt, 'sign': sign}

        r = requests.post(self.url, params=payload, headers=headers)
        if r.status_code == 503:
            return {"status_code": r.status_code}

        result = r.json()
        return result

    @staticmethod
    def concat_result(call_result):
        trans_result = call_result['trans_result']
        result_list = []
        for i in trans_result:
            result_list.append(i['dst'])
        return '\n'.join(result_list)


def get_translate_api(path="__APIKEY__"):
    with open(path, "r") as f:
        data = f.read().strip().split()
        assert len(data) >= 2, "__APIKEY__文件不全"
        return data[0], data[1]


def nbt_get(nbt, path):
    for i in path:
        nbt = nbt.get(i, {})
    return nbt


def nbt_set(nbt, path, target):
    for key in path[:-1]:
        nbt = nbt[key]
    nbt[path[-1]] = target


def load_snbt2nbt(filepath):
    with open(filepath, "r", encoding='utf-8') as f:
        return RelaxedParser(nbtlib.tokenize(f.read())).parse()


def save_nbt2snbt(nbt, filepath):
    with open(filepath, "w", encoding='utf-8') as f:
        f.write(nbtlib.serialize_tag(nbt, indent=4))
