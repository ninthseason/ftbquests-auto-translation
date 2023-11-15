import time
from tqdm import tqdm
from utils import *

translate_client = BaiduTranslateClient(*get_translate_api())


def deal_one_reward_table(reward_table_nbt, sleep_time=0.1):
    todo_list = []
    if 'rewards' in reward_table_nbt:
        for i in range(len(reward_table_nbt['rewards'])):
            if 'title' in reward_table_nbt['rewards'][i]:
                todo_list.append(['rewards', i, 'title'])
    todo_list.append(['title'])

    pbar = tqdm(total=len(todo_list))
    while len(todo_list) > 0:
        path = todo_list.pop()
        pbar.update(1)
        raw_desc = nbt_get(reward_table_nbt, path)
        if raw_desc is None:
            print(f"Warning: {path} description is None")
            continue
        desc = str_preprocess(str(raw_desc))
        if len(desc) == 0:
            continue
        callapi_response = translate_client.callapi(desc)
        if 'status_code' in callapi_response:
            print(f"Warning: {path} translate failed with code {callapi_response['status_code']}, is going to retry")
            todo_list.append(path)
            pbar.update(-1)
        else:
            t_description = translate_client.concat_result(callapi_response)
            nbt_set(reward_table_nbt, path, nbtlib.String(t_description + f"({desc})"))
            print(f"replace {path}")
            time.sleep(sleep_time)
    pbar.close()


if __name__ == '__main__':
    import argparse
    import os

    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", help="reward_table文件夹路径")
    parser.add_argument("-o", "--output", help="输出路径，默认为输入路径(覆盖)，需要文件夹存在", default="")
    # parser.add_argument("-v", "--verbose", help="详细输出")
    # parser.add_argument("-s", "--single", action="store_true", help="单文件处理(将-i视为文件路径)")
    args = parser.parse_args()
    print(args)
    chapter_folder_path = args.input
    out_path = args.output
    if out_path == "":
        out_path = chapter_folder_path
    # single_flag = args['single']

    files = os.listdir(chapter_folder_path)
    for filename in files:
        print(f"Deal with {filename}")
        nbt = load_snbt2nbt(os.path.join(chapter_folder_path, filename))
        deal_one_reward_table(nbt)
        save_nbt2snbt(nbt, os.path.join(out_path, filename))
