import json
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('-f', '--file', required=True, help='File to analyze')
args = parser.parse_args()

with open(args.file, 'r', encoding='utf-8') as f:
    data = json.load(f)

topic_dict = {}
index_dict = {}
for idx in data:
    el = data[idx]
    if 'topic' in el:
        topic = el['topic']
        l = [i.strip() for i in topic.split(';')]
        for i in l:
            if '=' in i:
                tr_en_split = i.split('=')
                str_t = tr_en_split[1].strip().lower()
            else:
                str_t = i.lower()
            if str_t == '':
                continue
            if str_t not in topic_dict:
                topic_dict[str_t] = 0
            topic_dict[str_t] += 1
    if 'index' in el:
        index = el['index']
        l = [i.strip() for i in index.split(';')]
        for i in l:
            if '=' in i:
                tr_en_split = i.split('=')
                str_t = tr_en_split[1].strip().lower()
            else:
                str_t = i.lower()
            if str_t == '':
                continue
            if str_t not in index_dict:
                index_dict[str_t] = 0
            index_dict[str_t] += 1

topic_dict = {k: v for k, v in sorted(topic_dict.items(), key=lambda item: item[1], reverse=True)}
with open('topic_dict.json', 'w', encoding='utf-8') as f:
    json.dump(topic_dict, f, ensure_ascii=False, indent=4)

index_dict = {k: v for k, v in sorted(index_dict.items(), key=lambda item: item[1], reverse=True)}
with open('index_dict.json', 'w', encoding='utf-8') as f:
    json.dump(index_dict, f, ensure_ascii=False, indent=4)