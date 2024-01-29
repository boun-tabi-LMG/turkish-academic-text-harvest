import re
import pandas as pd
from tika import parser
from pathlib import Path
from multiprocessing import Pool, context
from collections import Counter
from thesis_preprocessor import process_thesis_text
from pyinstrument import Profiler
# from langdetect import detect
from normalize import preprocess_text
import langid
import argparse
import math
import os
import logging

import warnings
warnings.simplefilter(action='ignore', category=UserWarning)

logger = logging.getLogger(__name__)
level = logging.INFO
logger.setLevel(level)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# handler for console info messages
ch = logging.StreamHandler()
ch.setFormatter(formatter)
ch.setLevel(level)
logger.addHandler(ch)

# handler for file info messages
fh = logging.FileHandler('log.txt')
fh.setFormatter(formatter)
fh.setLevel(level)
logger.addHandler(fh)

def is_turkish_content(text):
    """
    Determines if the given text is in Turkish.

    Returns:
        bool: True if the text is in Turkish, False otherwise.
    """
    try:
        # detected_language = detect(text) # lower() yaparsak langdetect basliklara isimlere turkce diyor, yoksa onlardan kurtulabiliyoruz.
        detected_language = langid.classify(text)[0]
        if detected_language == 'tr':
            return True
        else:
            return False
    except:
        return False

def remove_punctuation(text):
    """Removes punctuation marks from a given text."""
    punctuation = "!\"#$%&'()*+,-./:;<=>?@[\]^_`{|}~"
    for mark in punctuation:
        text = text.replace(mark, '')
    return text

def count_characters(line):
    """Counts the number of characters in a line of text."""
    return len(line)

def digit_ratio(line):
    """Calculates the ratio of digits in a line of text."""
    return sum(c.isdigit() for c in line) / len(line)

def uppercase_ratio(line):
    """Calculates the ratio of uppercase letters in a line of text."""
    return sum(c.isupper() for c in line) / len(line)

def capture_tokens(line):
    """Captures tokens (words) from a line of text."""
    tokens = line.split()
    return tokens

def compute_average_token_length(tokens):
    """
    Computes the average length of tokens (words).

    Returns:
        float: The average token length, or -1 if the tokens list is empty.
    """
    return sum(len(token) for token in tokens) / len(tokens) if tokens else -1

def capture_numbers(line):
    """Captures numbers from a line of text using regular expressions."""
    numbers = re.findall(r'\b\d+(?:\.\d+)?\b', line)
    return numbers

email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')

def check_email(line):
    """
    Checks if a line of text contains an email address.

    Returns:
        bool: True if an email address is found, False otherwise.
    """
    email_search = email_pattern.search(line)
    return bool(email_search)
    
# Two or three names in the format: "Gözde Serap Gökmen" or "Gözde Serap"
name_pattern_1 = re.compile(r"([A-ZÖÇŞİĞÜ][a-zöçşığü]*)([\s-]([A-ZÖÇŞİĞÜ][a-zöçşığü]*)){1,2}")
# Two or three names in the format: "Gözde SERAP Gökmen" or "Gözde SERAP"
name_pattern_2 = re.compile(r"([A-ZÖÇŞİĞÜ][a-zöçşığü]*)[\s-]([A-ZÖÇŞİĞÜ]*)([\s-][A-ZÖÇŞİĞÜ][a-zöçşığü]*)?")
# Two or three names in the format: "GÜNEY, Kerem. " or "GÜNEY, Kerem Ali. "
name_pattern_3 = re.compile(r"([A-ZÖÇŞİĞÜ]*),([\s-][A-ZÖÇŞİĞÜ][a-zöçşığü]*){1,2}.")

def check_name(line):
    """
    Checks if a line of text contains a name. Looks for exact match, not partial matches.
    Works only for lines that contain two or three tokens. 

    Returns:
        bool: True if a name comprises the line, False otherwise.
    """

    if len(line.strip().split(" ")) in [2, 3]:
        name_search_1 = name_pattern_1.fullmatch(line)
        name_search_2 = name_pattern_2.fullmatch(line)
        name_search_3 = name_pattern_3.fullmatch(line)
        name_search = bool(name_search_1 or name_search_2 or name_search_3)
        return name_search
    else:
        return False

def count_occurrence(lines_without_numbers, target_line):
    """
    Counts the number of occurrences of a target line in a list of lines.

    Returns:
        int: The number of occurrences.
    """
    strip_t = target_line.strip()
    number_removed = re.sub(r'(^(\d+)|(\d+)$)', '', strip_t)
    return lines_without_numbers.count(number_removed)

caption_items = ['Tablo', 'Şekil', 'Fotoğraf', 'Figür', 'Resim', 'Plan', 'Nota', 'Çizelge', 'Grafik', 'Ek', 'Levha', 'Harita']
caption_pattern = re.compile(fr"^({'|'.join(caption_items)})\s\d+[\.\:\-]")

def find_caption_type(line):
    """
    Determines the type of a caption line (e.g., table, figure, etc.).

    Returns:
        str: The caption type if matched, 'Yok' (meaning 'None') otherwise.
    """
    match = caption_pattern.search(line)
    if match:
        return match.group(1)
    return 'Yok'

number_at_beginning_pattern = re.compile(r'^(\d+)(?!\.\d)(\.?\s)?')
number_at_end_pattern = re.compile(r'(\d+)$')

def capture_number_at_beginning(text):
    """
    Captures the number at the beginning of a text.

    Returns:
        int: The captured number, or None if no number is found.
    """
    match = number_at_beginning_pattern.match(text.strip())
    if match:
        return int(match.group(1).strip())
    else:
        return None

def capture_number_at_end(text):
    """
    Captures the number at the end of a text.

    Returns:
        int: The captured number, or None if no number is found.
    """
    match = number_at_end_pattern.search(text.strip()[::-1])
    if match:
        return int(match.group(1).strip()[::-1])
    return None

def capture_dates(line):
    """
    Captures dates in various formats from a line of text.

    Returns:
        list: A list of tuples representing the captured dates.
    """
    date_formats = [
        r'\b(\d{1,2})/(\d{1,2})/(\d{4})\b',         # MM/DD/YYYY
        r'\b(\d{1,2})-(\d{1,2})-(\d{4})\b',         # MM-DD-YYYY
        r'\b(\d{1,2})\.(\d{1,2})\.(\d{4})\b',       # MM.DD.YYYY
        r'\b(\d{4})/(\d{1,2})/(\d{1,2})\b',         # YYYY/MM/DD
        r'\b(\d{4})-(\d{1,2})-(\d{1,2})\b',         # YYYY-MM-DD
        r'\b(\d{4})\.(\d{1,2})\.(\d{1,2})\b',       # YYYY.MM.DD
        r'\b(\d{1,2})\s(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s(\d{4})\b',  # DD Mon YYYY
    ]

    dates = []
    for date_format in date_formats:
        matches = re.findall(date_format, line)
        dates.extend(matches)

    return dates

def compute_affiliation_ratio(line):
    """
    Computes the count of affiliation-related terms in a line of text.

    Returns:
        float: The affiliation count ratio.
    """
    indicators = ['Prof', 'Doç', 'Yrd', 'Arş', 'Dr', 'Öğr', 'Gör', 'Üniversite', 'Enstitü', 'Fakülte', 'MYO', 'Assoc', 'Assc', 'Asst', 'Danışman', 'Anabilim', 'Anabilim Dalı', "Sayfa:", "Yüksek Lisans Tezi", "Doktora Tezi", "Yıl:"]
    # Manually created upper_indicators due to Anabilim.upper() --> ANABILIM, not ANABİLİM
    upper_indicators = ['PROF', 'DOÇ', 'YRD', 'ARŞ', 'DR', 'ÖĞR', 'GÖR', 'ÜNİVERSİTE', 'ENSTİTÜ', 'FAKÜLTE', 'MYO', 'ASSOC', 'ASSC', 'ASST', 'DANIŞMAN', 'ANABİLİM', 'ANABİLİM DALI', 'SAYFA:', 'YÜKSEK LİSANS TEZİ', 'DOKTORA TEZİ', 'YIL:']
    cities = [ "Adalar", "Adana", "Adıyaman", "Afyonkarahisar", "Ağrı", "Akçaabat", "Akçakale", "Akdeniz", "Akhisar", "Aksaray", "Alanya", "Alaşehir", "Altındağ", "Amasya", "Ankara", "Antalya", "Ardahan", "Arnavutköy", "Artvin", "Avcılar", "Aydın", "Bağcılar", "Bağlar", "Balıkesir", "Bandırma", "Bartın", "Batman", "Battalgazi", "Bayburt", "Bergama", "Beykoz", "Beylikdüzü", "Bilecik", "Bingöl", "Bitlis", "Bodrum", "Bolu", "Bornova", "Buca", "Burç", "Burdur", "Bursa", "Büyükçekmece", "Çağlayan", "Çanakkale", "Çankaya", "Çankırı", "Çarşamba", "Çayırova", "Çekme", "Çerkezköy", "Ceyhan", "Cizre", "Çorlu", "Çorum", "Darıca", "Değirmendere", "Denizli", "Diyarbakır", "Doğubayazıt", "Düzce", "Edirne", "Edremit", "Elazığ", "Elbistan", "Ereğli", "Erenler", "Ergani", "Erzincan", "Erzurum", "Esenler", "Esenyurt", "Eskişehir", "Etimesgut", "Fatsa", "Fethiye", "Gaziantep", "Gaziemir", "Gebze", "Giresun", "Gölcük", "Gümüşhane", "Güngören", "Hadımköy", "Hakkari", "Hatay", "Iğdır", "İnegöl", "İskenderun", "Isparta", "İstanbul", "Istanbul", "Izmir", "Kadirli", "Kağıthane", "Kahramanmaraş", "Kahta", "Kapaklı", "Karadeniz", "Karabük", "Karaköprü", "Karaman", "Karatepe", "Kars", "Karşıyaka", "Kartal", "Kastamonu", "Kayapınar", "Kayseri", "Kazanlı", "Kazımpaşa", "Keçiören", "Kemalpaşa", "Kemerburgaz", "Kilis", "Kırıkkale", "Kırklareli", "Kırşehir", "Kızıltepe", "Kocaeli", "Konak", "Konya", "Körfez", "Kozan", "Küçükçekmece", "Kuşadası", "Kütahya", "Lüleburgaz", "Mahmut Şevket Paşa", "Mahmutbey", "Malatya", "Mamak", "Manavgat", "Manisa", "Mardin", "Marmara", "Melikgazi", "Menemen", "Meram", "Mersin", "Midyat", "Muğla", "Muş", "Nazilli", "Nevşehir", "Niğde", "Nizip", "Nusaybin", "Ödemiş", "Ordu", "Osmaniye", "Pamukkale", "Patnos", "Pendik", "Polatlı", "Pursaklar", "Rize", "Sakarya", "Salihli", "Samandağ", "Samandıra", "Samsun", "Şanlıurfa", "Sarıyer", "Selçuklu", "Serdivan", "Serik", "Seyhan", "Siirt", "Silifke", "Silivri", "Silopi", "Sincan", "Sinop", "Şırnak", "Sivas", "Siverek", "Söke", "Soma", "Sultanbeyli", "Suruç", "Talas", "Tarsus", "Tavşanlı", "Tekirdağ", "Trakya", "Tokat", "Torbalı", "Trabzon", "Tunceli", "Turgutlu", "Tuzla", "Ünye", "Uşak", "Van", "Viranşehir", "Yalova", "Yenice", "Yenimahalle", "Yenişehir", "Yeşilyurt", "Yolboyu", "Yozgat", "Yüksekova", "Yüreğir", "Zonguldak"]

    no_indicators = len([indicator for indicator in indicators if indicator in line])
    no_upper_indicators = len([indicator for indicator in upper_indicators if indicator in line])
    no_cities = len([i for i in cities if i in line])

    affiliation_ratio = (no_indicators + no_upper_indicators + (no_cities > 0)) / (len(indicators)+1)

    return affiliation_ratio

inline_citation_pattern = re.compile('[\(\[](([A-Za-zöÖçÇşŞıİğĞüÜ&–§¶\s\d\',:;\.-]+[\s,])?[\d\.]*)((: ?|, ?s.) ?\d+(-\d+)?)?[\)\]]', re.MULTILINE)
reference_pattern = re.compile('[A-Za-zöÖçÇşŞıİğĞüÜ&–§¶\s\d\',:\.\(\)]+(19|20)\d{2}', re.MULTILINE)
pp_pattern = re.compile('[\(\s]pp\.?\s?\d+', re.MULTILINE)

def capture_citations(text):
    """
    Checks if a text contains any citations using a regular expression pattern.

    Returns:
        bool: True if citations are found, False otherwise.
    """
    return bool(inline_citation_pattern.search(text)) or bool(reference_pattern.search(text)) or bool(pp_pattern.search(text))

def discard_flags(text):
    """
    Checks if a text contains any citations using a regular expression pattern.

    Returns:
        bool: True if citations are found, False otherwise.
    """
    tokens = ['ORCID', 'DOI', '.....']
    if any(token in text for token in tokens):
        return True
    return False

volume_pattern = re.compile(r"vol\s*\d+\s*.+no\s\d+\s*.+p")
volume_tr_pattern = re.compile(r"cilt\s*\d+\s*.+sayı\s\d+\s*.+s")

def check_volume_number_format(text):
    """
    Checks if a text follows a specific volume and number format.

    Returns:
        bool: True if the format is matched, False otherwise.
    """

    match = volume_pattern.search(text)
    tr_match = volume_tr_pattern.search(text)
    return bool(match) or bool(tr_match)

def parse_pdf(path):
    """
    Parses a PDF file and extracts the content as a list of stripped lines.

    Args:
        path (str): The path to the PDF file.

    Returns:
        list: A list of stripped lines from the PDF content.
    """
    parsed = parser.from_file(path)
    return [l.strip() for l in parsed["content"].split('\n') if l.strip() != '']

index_str_l = ['tablo', 'şekil', 'grafik', 'çizelge', 'table', 'figure', 'graph', 'chart', 'plan', 'resim', 'figür', 'levha', 'simge', 'harita', 'fotoğraf',
               'tablolar', 'şekiller', 'grafikler', 'çizelgeler', 'resimler', 'figürler', 'levhalar', 'planlar', 'simgeler', 'haritalar', 'fotoğraflar',
                'tabloların', 'şekillerin', 'fotoğrafların', 'figürlerin', 'resimlerin', 'planların', 'notaların', 'çizelgelerin', 'grafiklerin', 'eklerin', 'levhaların', 'haritaların']
index_heading_pattern = re.compile(r'(dizini?|listesi|^kisaltmalar)$', re.IGNORECASE)
index_start_pattern = re.compile(r'^(' + '|'.join(index_str_l) + r')(.?)\s*\d+', re.IGNORECASE)

def check_index(lines):
    """
    Checks if a line is part of an index.

    Returns:
        bool: True if the line is part of an index, False otherwise.
    """
    if len(lines) != 3:
        return False
    prev_line, current_line, next_line = lines
    current_line = current_line.lower().replace('i̇', 'i').strip()
    if index_heading_pattern.search(current_line) or index_heading_pattern.search(prev_line):
        return True
    next_line = next_line.lower().replace('i̇', 'i').strip()
    if index_start_pattern.search(current_line):
        return True
    prev_line = prev_line.lower().replace('i̇', 'i').strip()
    if index_start_pattern.search(prev_line):
        return True
    return False

def compute_line_statistics(lines):
    """
    Computes various statistics for each line in a list of lines.

    Returns:
        list: A list of dictionaries containing the line statistics.
    """

    # create a list consisting of `lines` with numbers removed
    lines_without_numbers = [re.sub(r'(^(\d+)|(\d+)$)', '', line.strip()) for line in lines]

    statistics = []
    for i, line in enumerate(lines):
        stats = {'line': line}
        #stats['is_turkish'] = is_turkish_content(line)
        stats['characters'] = count_characters(line)
        stats['tokens'] = capture_tokens(line)
        stats['numbers'] = capture_numbers(line)
        stats['token_count'] = len(stats['tokens'])
        stats['number_count'] = len(stats['numbers'])
        stats['average_token_length'] = compute_average_token_length(stats['tokens'])
        stats['number_ratio'] = len(stats['numbers']) / len(stats['tokens']) if stats['tokens'] else -1
        stats['digit_ratio'] = digit_ratio(line)
        stats['uppercase_ratio'] = uppercase_ratio(line)
        stats['dates'] = capture_dates(line)
        stats['has_email'] = check_email(line)
        stats['has_name'] = check_name(line)
        stats['occurrence'] = count_occurrence(lines_without_numbers, line)
        stats['caption_type'] = find_caption_type(line)
        stats['affiliation_count'] = compute_affiliation_ratio(line)
        stats['citation_format'] = check_volume_number_format(line)
        stats['discard_flag'] = discard_flags(line)
        stats['initial_number'] = capture_number_at_beginning(line)
        stats['final_number'] = capture_number_at_end(line)
        stats['has_citation'] = capture_citations(line)
        stats['part_of_index'] = check_index(lines[i-1:i+2])

        statistics.append(stats)
    return statistics

def correct_false_values(df, column_name):
    """
    Corrects false values in a DataFrame column based on surrounding values.

    Returns:
        pd.DataFrame: The updated DataFrame with corrected values.
    """
    for i in range(len(df)):
        if not df[column_name].iloc[i]:
            start_index = max(0, i - 5)
            end_index = min(i + 6, len(df))
            window = df[column_name].iloc[start_index:end_index]
            true_count = window[window].count()
            if true_count >= 0.9 * len(window):
                df.loc[i, f'{column_name}_corrected'] = True

    return df

def mark_items(df, window_size=5, threshold_token_count=2, threshold_drop_ratio=0.5):
    # Mark items based on conditions
    df['item'] = False
    conditions = (df['digit_ratio'] >= 0.2) & (df['average_token_length'] < 4)
    df.loc[conditions, 'item'] = True

    no_items_to_mark = sum( df['caption_type'] != 'Yok' )
    if no_items_to_mark > 25:
        logger.info(f'Skipping marking {no_items_to_mark} items...')
        return df
    
    # Iterate through the DataFrame
    for i, row in df.iterrows():
        if row['caption_type'] != 'Yok':
            left_index = max(0, i - window_size)
            right_index = min(i + window_size + 1, len(df))
            
            left_window = df.loc[left_index:i]
            right_window = df.loc[i+1:right_index]
            
            left_token_count = left_window['token_count'].mean()
            right_token_count = right_window['token_count'].mean()
            
            left_true_count = left_window['item'].sum()
            right_true_count = right_window['item'].sum()
            
            if left_token_count <= right_token_count:
                current_index = i - 1 
                while current_index >= 0:
                    temp_window = df.loc[current_index - window_size - 1:current_index-1]
                    token_avg = temp_window['token_count'].mean()
                    drop_count = temp_window['item'].sum()
                    
                    if token_avg > threshold_token_count or drop_count / window_size < threshold_drop_ratio or current_index == 0:
                        last_index = min(temp_window[temp_window['token_count'] <= threshold_token_count].index.min(),
                                         temp_window[temp_window['item']].index.min())
                        if not pd.isnull(last_index):
                            df.loc[last_index:i-1, 'item'] = True
                            break
                    current_index -= 1
            else:
                current_index = i + 1
                while current_index < len(df):
                    temp_window = df.loc[current_index+1:i+window_size+1]
                    token_avg = temp_window['token_count'].mean()
                    drop_count = temp_window['item'].sum()
                    
                    if token_avg > threshold_token_count or drop_count / window_size < threshold_drop_ratio or current_index == len(df) - 1:
                        last_index = max(temp_window[temp_window['token_count'] <= threshold_token_count].index.max(),
                                         temp_window[temp_window['item']].index.max())
                        if not pd.isnull(last_index):
                            df.loc[i+1:last_index, 'item'] = True
                            break
                    current_index += 1
    return df

citation_after_word_pattern = re.compile('([a-zA-ZöÖçÇşŞıİğĞüÜ]+[\."\']*?)\d+', re.MULTILINE)

def merge_lines(df, min_page_length=50, page_end_context=250):
    # Create a new column to mark page breaks
    df['page_break'] = df['line'].apply(lambda s: '[PAGE_BREAK]' in s)
    # Create a new column with stripped lines
    df['line_stripped'] = df['line'].str.replace('\[PAGE_BREAK\]', '').str.strip()
    # Initialize variables
    current_page = ''
    overall_text = ''

    # Iterate through the DataFrame
    for i, row in df.iterrows():
        if row['line_stripped'].endswith('-'):
            current_page += row['line_stripped'].rstrip('- ')
        else:
            current_page += row['line_stripped'] + ' '
        # Check for a page break
        if row['page_break']:
            if current_page and len(current_page) > min_page_length:
                #page_end = current_page[-page_end_context:]
                # footnote_pattern = r'[.,;!?]\s?\d+\.\s.*$'
                # cleaned_page_end = re.sub(footnote_pattern, '', page_end).strip()
                # current_page = current_page[:-page_end_context] + cleaned_page_end
                overall_text += current_page + ' '
            current_page = ''

    overall_text += current_page + ' '
    return overall_text


bibliography_keywords = ['Bibliyoğrafya', 'Bibliyografya', 'Bibliyog', 'Kaynakça', 'Kaynaklar', 'Kaynaklar/References', 'Yararlanılan Kaynaklar']
bibliography_keywords += [' '.join(keyword) for keyword in bibliography_keywords] # Add the keywords with spaces: 'K A Y N A K L A R'
bibliography_pattern = re.compile(r'^(\d+\.?\s*?)?(' + '|'.join(bibliography_keywords) + r')\b', re.IGNORECASE)

def find_bibliography(df):
    # TODO: Handle the case where keywords are detected more than once.
    """
    Identifies the rows containing bibliography based on specific keywords.

    Returns:
        pd.DataFrame: The updated DataFrame with a column indicating the bibliography rows.
    """

    # Search for the keywords in the 'text_column'
    mask = df['line'].str.contains(r'^(\d+\.?\s*?)?(' + '|'.join(bibliography_keywords) + r')\b', case=False, na=False, regex=True)
    # Get the index of the row(s) containing the keywords
    row_indices = df[mask].index

    # If only one keyword is found
    if len(row_indices) == 1:
        bibliography_row_index = row_indices[0]
    # If more than one keyword is found, look for exact match or space after keyword, select the first match
    elif len(row_indices) > 1:
        matchFlag = False
        for i, row in df[mask].iterrows():
            match = bibliography_pattern.match(row["line"])
            if match:
                matchFlag = True
                bibliography_row_index = i
        # If no match is found, take the last row that contains a keyword
        if not matchFlag:
            bibliography_row_index = row_indices[-1]
    # If no keyword is found, bibliography doesn't exist
    else:
        assert len(row_indices) == 1

    df.loc[:bibliography_row_index, 'is_bibliography'] = False
    df.loc[bibliography_row_index:, 'is_bibliography'] = True
    return df

def mark_footnotes(df):
    """
    Marks the rows in the DataFrame that are footnotes based on consecutive numbering.

    Returns:
        pd.DataFrame: The updated DataFrame with a column indicating the footnote rows.
    """
    last_number = -1
    last_index = -1
    df['is_footnote'] = False
    df['initial_number'] = df['initial_number'].fillna(-1)

    for i in range(len(df)):
        current_number = df['initial_number'].iloc[i]
        gap = i - last_index
        df.loc[i, 'last - current'] = last_number - current_number
        if last_number > 0 and current_number > 0 and (current_number - last_number <= 2) and ((current_number - last_number > 0)) and gap <= 6:
            for j in range(last_index, i+1):
                df.loc[j, 'is_footnote'] = True

            last_number = current_number
            last_index = i

        else:
            if i != last_index + 1 and current_number != -1:
                last_number = current_number
                last_index = i

    return df

def replace_most_frequent_empty_lines(text):
    # Find all sequences of consecutive empty lines
    matches = re.findall(r"(?:\n\s*){2,}", text)

    # If no matches, return the original text
    if not matches:
        return text

    # Get the counts of consecutive empty lines
    counts = [len(match.split('\n')) for match in matches]
    
    # Find the most common count
    most_common, _ = Counter(counts).most_common(1)[0]
    if most_common < 5:
        return text
    # Replace the most common count of consecutive empty lines with the placeholder
    pattern_to_replace = r"(?:\n\s*){%d}" % most_common
    logger.info(f'Replacing {most_common} consecutive empty lines with the placeholder', )
    return re.sub(pattern_to_replace, ' [PAGE_BREAK]\n', text)

def remove_text_before_abstract(text):
    """Removes the text before the abstract section."""
    keyword_pattern = r'\b(?:ÖZET|ÖZ|Öz|Özet)\s*?\n'
    match = re.search(keyword_pattern, text)
    
    if match and (match.group(0).strip() in ["ÖZET", "ÖZ", "Öz", "Özet"]):
        start_index = match.start()
        # Make sure that the abstract appears in the first half. 
        if start_index < len(text)/2:
            text = text[start_index:]
    return text

def convert_pdf_to_text(file, is_thesis, output_dir, detect_language=True):
    """
    Converts a PDF file to text, performs text analysis, and saves the results to a CSV file.

    The function reads the PDF file, computes line statistics, and identifies various line types
    such as footnotes, bibliography, etc. The processed results are then saved to a CSV file.

    Args:
        file (str): The path to the PDF file.
    """
    logger.info(f'Processing {file}')
    file_path = Path(file)
    no_inline_folder = Path(output_dir)
    no_inline_folder.mkdir(parents=True, exist_ok=True)

    no_inline_filename = no_inline_folder / file_path.name
    
    if file.endswith('pdf'):
        no_inline_filename = str(no_inline_filename).replace('.pdf','_no_inline_citations.txt')
    elif file.endswith('txt'):
        no_inline_filename = str(no_inline_filename).replace('.txt','_no_inline_citations.txt')

    if file.endswith('.pdf'):
        try:
            content = parser.from_file(file)['content']
        except:
            logger.info('Error during OCR {file}')
            return
        
    elif file.endswith('.txt'):
        with open(file, encoding='utf-8') as f:
            content = f.read()

    if content.strip() == '': 
        logger.info('Empty file')
        return 

        
    logger.info(f'Preprocessing and removing text before abstract')
    content = preprocess_text(content)
    content = remove_text_before_abstract(content)
    if is_thesis: 
        logger.info(f'Performing thesis preprocessing')
        content = process_thesis_text(content)
    else:
        content = replace_most_frequent_empty_lines(content)

    logger.info('Computing line statistics')
    lines = [l.strip() for l in content.split('\n') if l.strip()]
    df = pd.DataFrame(compute_line_statistics(lines))
    df['final_number'] = df['final_number'].fillna(-1)
    logger.info(f'Initial number of lines {df.shape[0]}')
    try:
        # Bibliography is not present in all pdfs.
        logger.info('Finding bibliography')
        df = find_bibliography(df)
    except:
        df['is_bibliography'] = False

    df.drop(df.loc[(df['is_bibliography'] == True)
                   | df['has_email']
                   | df['has_name']
                   | df['citation_format']
                   | df['discard_flag']
                   | (df['affiliation_count'] > 0.09)
                   | (df['occurrence'] > 2)].index, inplace=True)
    logger.info(f'Number of lines after dropping bibliography and some other items {df.shape[0]}')

    if df.shape[0] == 0:
        logger.info('No content left after filtering.')
        return

    df.reset_index(drop=True, inplace=True)

    if detect_language:
        logger.info(f'Detecting language and correcting values')
        df['is_turkish'] = df['line'].apply(is_turkish_content)
        df['is_turkish_corrected'] = df['is_turkish']
        df = correct_false_values(df, 'is_turkish')
        df.drop(df.loc[df['is_turkish_corrected'] == False].index, inplace=True)

    logger.info(f'Number of lines after dropping non-Turkish content {df.shape[0]}')

    if df.shape[0] == 0:
        logger.info('No content left after filtering.')
        return
   
    df.reset_index(drop=True, inplace=True)

    logger.info(f'Marking footnotes')
    df = mark_footnotes(df)
    logger.info(f'Marking table items for {len(df)} lines')
    df = mark_items(df)

    index = df[((df['digit_ratio'] >= 0.2) & (df['average_token_length'] < 4)) # usually table values
                | (df['digit_ratio'] == 1)                                        # page numbers
                | (df['number_ratio'] > 1)                                        # numbers
                | (df['item'] == True)
                | (df['has_email'])
                | (df['caption_type'] != 'Yok')
                | (df['is_footnote'])
                | (df['citation_format'])
                | (df['discard_flag'])
                | (df['affiliation_count'] > 0.09)
                | (df['occurrence'] > 2)
                | (df['is_bibliography'])
                | (df['part_of_index'])].index

    df.loc[index, 'drop'] = True

    df = correct_false_values(df, 'drop')

    if df.shape[0] == 0:
        logger.info('No content left after filtering.')
        return

    filtered_df = df.drop(index)

    logger.info(f'Final number of lines {filtered_df.shape[0]}')

    logger.info(f'Merging lines {filtered_df.shape[0]}')

    filtered_content = merge_lines(filtered_df)
    no_inline_content = re.sub(inline_citation_pattern, '', filtered_content)
    no_citation_after_word_content = re.sub(citation_after_word_pattern, '\\1', no_inline_content)
    with open(no_inline_filename, 'w', encoding='utf-8') as f:
        f.write(no_citation_after_word_content)

def wrapper_convert(args_tuple):
    try:
        input_file, thesis_preprocessing, output_dir = args_tuple
        return convert_pdf_to_text(input_file, thesis_preprocessing, output_dir)
    except Exception as e:
        logger.info(f'Error during conversion of {input_file}: {e}')

def profiler_convert(input_tuples, count): 
    for input_tuple in input_tuples[:count]:
        convert_pdf_to_text(*input_tuple)
    
def main():
    arg_parser = argparse.ArgumentParser(description='Extracts text from PDF files.')
    arg_parser.add_argument('-p', '--path', type=str, help='The path to the PDF folder or file.', required=True)
    arg_parser.add_argument('-o', '--output', type=str, help='The path to the output directory.', required=True)
    arg_parser.add_argument('-n', '--num_threads', type=int, help='The number of threads to use.', default=4)
    arg_parser.add_argument('-l', '--time_limit', type=int, help='The time limit for each conversion in seconds.', default=30)
    arg_parser.add_argument('-t', '--thesis_preprocessing',  action='store_true', help='Enable thesis preprocessing during conversion.')
    arg_parser.add_argument('-s', '--skip',  action='store_true', help='Skip files that already exist in the output directory.')
    arg_parser.add_argument('-d', '--detect_language',  action='store_true', help='Detect language and correct values.')
    arg_parser.add_argument('-i', '--profiler',  type=int, help='Enable profiler to measure performance of provided no. of files.', default=0)
    args = arg_parser.parse_args()

    input_path = Path(args.path)
    if input_path.is_file() and (input_path.name.endswith('.pdf') or input_path.name.endswith('.txt')):
        input_files = [input_path]
    elif input_path.is_dir():
        input_files = [f for f in input_path.iterdir() if (f.name.endswith('.pdf') or f.name.endswith('.txt'))]

    if args.skip: 
        output_files = [f.name.replace('_no_inline_citations.txt', '') for f in Path(args.output).iterdir()]
        input_files = [input_file for input_file in input_files if input_file.name.replace('.txt', '') not in output_files]

    input_tuples = [(str(input_file), args.thesis_preprocessing, args.output) for input_file in input_files]

    if args.profiler == 0:
        with Pool(args.num_threads) as pool:
            results = [pool.apply_async(wrapper_convert, (input_tuple,)) for input_tuple in input_tuples]
            for r, input_file in zip(results, input_files):
                try:
                    r.get(timeout=args.time_limit)  
                except context.TimeoutError:
                    logger.info(f"Conversion timed out for file: {input_file}")
    else:
        with Profiler(interval=0.1) as profiler:
            profiler_convert(input_tuples, args.profiler)
        profiler.print()
        profiler.open_in_browser()

if __name__ == '__main__':
    main()
