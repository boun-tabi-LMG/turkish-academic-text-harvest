import re
from collections import Counter

def find_most_frequent_empty_line_count(text):
    """
    Determine the most frequent count of consecutive empty lines in the given text.
    
    :param text: str - Input text to analyze.
    :return: tuple (int, int) - A tuple containing the most frequent count of consecutive empty lines and its frequency.
    """
    matches = re.findall(r"(?:\n\s*){2,}", text)
    if not matches:
        return 0, 0

    counts = [len(match.split('\n')) for match in matches]
    most_common_count, frequency = Counter(counts).most_common(1)[0]
    return most_common_count, frequency

def insert_page_breaks(text):
    """
    Replace the most frequent count of consecutive empty lines with a placeholder.
    
    :param text: str - Input text to modify.
    :return: str - Text with placeholders replacing the most common count of consecutive empty lines.
    """
    most_common_count = find_most_frequent_empty_line_count(text)[0]
    if most_common_count == 0:
        return text
    
    pattern_to_replace = r"(?:\n\s*){%d}" % most_common_count
    return re.sub(pattern_to_replace, '\n[PAGE_BREAK]\n', text)


def remove_text_between_patterns(text, pattern):
    """
    Remove text that lies between the provided pattern.
    
    :param text: str - Input text to modify.
    :param pattern: str - Pattern indicating sections to remove.
    :return: str - Text with specified sections removed.
    """
    return re.sub(pattern, '', text, flags=re.IGNORECASE)

def replace_roman_numbers_with_placeholder(text):
    pattern = r"\n\s*?(?:I|II|III|IV|V|VI|VII|VIII|IX|X|XI|XII|XIII|XIV|XV|XVI|XVII|XVIII|XIX|XX)\s*?\n"
    return re.sub(pattern, r'\n[ROMAN_PAGE_NUMBER]\n', text, flags=re.IGNORECASE)

def replace_page_numbers_with_placeholder(text):
    pattern = r"\n(\s)?(\d+)(?!\.\d)(\.?\s)?\n"
    return re.sub(pattern, r'\n[PAGE_NUMBER]\n', text)

SECTIONS_TO_DISCARD  = ['ÖZGEÇMİŞ', 'ÖNSÖZ', 'ÖN SÖZ', 'BEYAN', 'BİLDİRİM', 'TEŞEKKÜR', 'JÜRİ VE ENSTİTÜ ONAYI', 'ETİK KURUL ONAYI', 'TEZ ONAY FORMU', 
                        'TEZ KABUL VE ONAYI', 'DOĞRULUK BEYANI', 'KISALTMALAR', 'YEMİN', 'TUTANAK', 'TEZ BİLDİRİMİ',  #'İÇİNDEKİLER', 
                        'BİLİMSEL ETİĞE UYGUNLUK', 'TEZ YAZIM KLAVUZUNA UYGUNLUK', 'İTHAF', 'EKLER',  'ÇİZELGE LİSTESİ', 'KISALTMALAR\s+LİSTESİ'
                        #   'RESİM LİSTESİ','PLAN LİSTESİ', 'GRAFİK LİSTESİ', 'TABLO LİSTESİ', 'ŞEKİL LİSTESİ', 'FİGÜR LİSTESİ', 'ÇİZELGE LİSTESİ', 'LEVHA LİSTESİ', 'NOTA LİSTESİ',
                        #   'RESİM DİZİNİ','PLAN DİZİNİ', 'GRAFİK DİZİNİ', 'TABLO DİZİNİ', 'ŞEKİL DİZİNİ', 'FİGÜR DİZİNİ', 'ÇİZELGE DİZİNİ', 'LEVHA DİZİNİ', 'NOTA DİZİNİ',
                    ]

PLACEHOLDER_PATTERN = r'\[PAGE_BREAK\]' # r'(\[ROMAN_PAGE_NUMBER\])|\[PAGE_NUMBER\]|\[PAGE_BREAK\])'
DISCARD_TEXT_PATTERN  = r'(' + '|'.join(SECTIONS_TO_DISCARD )  + r')\n+?[\s\S]*?' + PLACEHOLDER_PATTERN 
ALTERNATIVE_DISCARD_TEXT_PATTERN  = r'(' + '|'.join(["ÖNSÖZ", "ÖN SÖZ", "TEŞEKKÜR"])  + r')[\s\S]*?' + PLACEHOLDER_PATTERN +  r'[\s\S]*?' + PLACEHOLDER_PATTERN 


def process_thesis_text(text):
    """
    Process and clean thesis text: 
    1. Marks sections with Roman and page numbers.
    2. Replaces the most frequent empty line sequence with a page break placeholder.
    3. Removes specified sections from the thesis.
    
    :param text: str - Thesis text to be processed.
    :return: str - Processed text.
    """
    text = replace_roman_numbers_with_placeholder(text)
    text = replace_page_numbers_with_placeholder(text)
    text = insert_page_breaks(text)
    text = text.replace('ROMAN_PAGE_NUMBER', 'PAGE_BREAK')
    text = text.replace('PAGE_NUMBER', 'PAGE_BREAK')  
    text = remove_text_between_patterns(text, DISCARD_TEXT_PATTERN)
    text = remove_text_between_patterns(text, ALTERNATIVE_DISCARD_TEXT_PATTERN)
    return text 