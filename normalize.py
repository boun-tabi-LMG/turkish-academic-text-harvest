from string import punctuation, ascii_lowercase, ascii_uppercase
from pathlib import Path
import json 

valid_chars = punctuation + ascii_lowercase + ascii_uppercase + "0123456789" + " " + "\n" + "é" + "üğişçöıÜĞİŞÇÖ"

def find_invalid_chars(files):
    invalid_dict = {}
    example_dict = {}
    for file in files:
        text = open(str(file), encoding="utf-8").read()
        for i, c in enumerate(text):
            if c not in valid_chars:
                if c in invalid_dict:
                    invalid_dict[c] += 1
                    if len(example_dict[c]) < 10 and invalid_dict[c] > 500:
                        example_dict[c].append((str(text[i-10:i+10]), str(file)))
                else:
                    invalid_dict[c] = 1
                    example_dict[c] = [(str(text[i-10:i+10]), str(file))]
    invalid_dict = sorted(invalid_dict.items(), key=lambda x:x[1], reverse=True)
    print(invalid_dict)
    print(example_dict)
    return invalid_dict, example_dict

#folder = "/truba/home/zyirmibesoglu/turkish_llm/media/disk/datasets/bounllm/dergipark/no_inline_txt"
#files = Path(folder).iterdir()
#invalid_dict, example_dict  = find_invalid_chars(files)

replacement_dict = {'“': '"',
 '’': "'",
 '”': '"',
 '—': "-",
 '‘': "'",
 '–': "-",
 '…': "...",
 '«': '"',
 '»': '"',
 '\xad ' : "",
 '\xad' : "",
 '\xa0': " ",
 "„": '"',
 "•": "",
 "–": "-",
 "~~~ ": "",
 "''": '"',
 "``": '"',
 "≈": "",
 "←": "",
 "►": "-",
 "›": "'",
 "\uf04a":"",
 "☺": ":)",
 "¦": "",
 "©":"",
 '\u200e' : "",
 "\'": "'",
 "\\'": "'",
 "\\\'": "'",
 "�": "",
 '›':"ı",
 'е':"e",
 'Ģ':"ş",
 'ý':"ı",
 'ā':"a",
 '‟':'"',
 '¤':"ğ",
 '\uf0b7':"",
 'õ':"ı",
 '\uf020':"",
 "Ġ": "İ",
 '\uf0bf': "",
 '\uf0bb': "",
 "ŋ": "n",
 "ð": "ğ",
 "ñ": "n",
 "À": "A",
 "í": "i",
 "ī": "i",
 "−": "-",
 "ÅŸ": "ş",
 "Ä±": "ı",
 "\uf0b4": "",
 "\uf0b2": "",
 "—": "-",
 "Ý": "ı",
 "Û": "ğ",
 "\uf0ae": "",
 "\uf001": "",
 "Đ": "İ',                   
}

def preprocess_sentence(line):
    for key, value in replacement_dict.items():
        line = line.strip().replace(key, value)
    return line
