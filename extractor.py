import re
import pandas as pd
from tika import parser
from langdetect import detect
from pathlib import Path
from multiprocessing import Pool
import argparse

def is_turkish_content(text):
    """
    Determines if the given text is in Turkish.

    Returns:
        bool: True if the text is in Turkish, False otherwise.
    """
    try:
        detected_language = detect(text) # lower() yaparsak basliklara isimlere turkce diyor, yoksa onlardan kurtulabiliyoruz.
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

def count_occurrence(lines_without_numbers, target_line):
    """
    Counts the number of occurrences of a target line in a list of lines.

    Returns:
        int: The number of occurrences.
    """
    strip_t = target_line.strip()
    number_removed = re.sub(r'(^(\d+)|(\d+)$)', '', strip_t)
    return lines_without_numbers.count(number_removed)

caption_items = ['Tablo', 'Şekil', 'Fotoğraf', 'Figür', 'Resim', 'Plan', 'Nota', 'Çizelge', 'Grafik', 'Ek']
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

number_at_beginning_pattern = re.compile(r'^(\d+)')
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
    indicators = ['Prof', 'Doç', 'Yrd', 'Arş', 'Dr', 'Öğr', 'Gör', 'Üniversite', 'Fakülte', 'MYO', 'Assoc', 'Assc', 'Asst']
    cities = [ "Adalar", "Adana", "Adıyaman", "Afyonkarahisar", "Ağrı", "Akçaabat", "Akçakale", "Akdeniz", "Akhisar", "Aksaray", "Alanya", "Alaşehir", "Altındağ", "Amasya", "Ankara", "Antalya", "Ardahan", "Arnavutköy", "Artvin", "Avcılar", "Aydın", "Bağcılar", "Bağlar", "Balıkesir", "Bandırma", "Bartın", "Batman", "Battalgazi", "Bayburt", "Bergama", "Beykoz", "Beylikdüzü", "Bilecik", "Bingöl", "Bitlis", "Bodrum", "Bolu", "Bornova", "Buca", "Burç", "Burdur", "Bursa", "Büyükçekmece", "Çağlayan", "Çanakkale", "Çankaya", "Çankırı", "Çarşamba", "Çayırova", "Çekme", "Çerkezköy", "Ceyhan", "Cizre", "Çorlu", "Çorum", "Darıca", "Değirmendere", "Denizli", "Diyarbakır", "Doğubayazıt", "Düzce", "Edirne", "Edremit", "Elazığ", "Elbistan", "Ereğli", "Erenler", "Ergani", "Erzincan", "Erzurum", "Esenler", "Esenyurt", "Eskişehir", "Etimesgut", "Fatsa", "Fethiye", "Gaziantep", "Gaziemir", "Gebze", "Giresun", "Gölcük", "Gümüşhane", "Güngören", "Hadımköy", "Hakkari", "Hatay", "Iğdır", "İnegöl", "İskenderun", "Isparta", "İstanbul", "Istanbul", "Izmir", "Kadirli", "Kağıthane", "Kahramanmaraş", "Kahta", "Kapaklı", "Karadeniz", "Karabük", "Karaköprü", "Karaman", "Karatepe", "Kars", "Karşıyaka", "Kartal", "Kastamonu", "Kayapınar", "Kayseri", "Kazanlı", "Kazımpaşa", "Keçiören", "Kemalpaşa", "Kemerburgaz", "Kilis", "Kırıkkale", "Kırklareli", "Kırşehir", "Kızıltepe", "Kocaeli", "Konak", "Konya", "Körfez", "Kozan", "Küçükçekmece", "Kuşadası", "Kütahya", "Lüleburgaz", "Mahmut Şevket Paşa", "Mahmutbey", "Malatya", "Mamak", "Manavgat", "Manisa", "Mardin", "Marmara", "Melikgazi", "Menemen", "Meram", "Mersin", "Midyat", "Muğla", "Muş", "Nazilli", "Nevşehir", "Niğde", "Nizip", "Nusaybin", "Ödemiş", "Ordu", "Osmaniye", "Pamukkale", "Patnos", "Pendik", "Polatlı", "Pursaklar", "Rize", "Sakarya", "Salihli", "Samandağ", "Samandıra", "Samsun", "Şanlıurfa", "Sarıyer", "Selçuklu", "Serdivan", "Serik", "Seyhan", "Siirt", "Silifke", "Silivri", "Silopi", "Sincan", "Sinop", "Şırnak", "Sivas", "Siverek", "Söke", "Soma", "Sultanbeyli", "Suruç", "Talas", "Tarsus", "Tavşanlı", "Tekirdağ", "Trakya", "Tokat", "Torbalı", "Trabzon", "Tunceli", "Turgutlu", "Tuzla", "Ünye", "Uşak", "Van", "Viranşehir", "Yalova", "Yenice", "Yenimahalle", "Yenişehir", "Yeşilyurt", "Yolboyu", "Yozgat", "Yüksekova", "Yüreğir", "Zonguldak"]

    return len([indicator for indicator in indicators if indicator in line] + [i for i in cities if i in line]) / (len(indicators)+1)

citation_pattern = re.compile('\(([A-Za-z–§¶\s\d\',:]+[\s,]\d{4}|\d+)\)', re.MULTILINE)

def capture_citations(text):
    """
    Checks if a text contains any citations using a regular expression pattern.

    Returns:
        bool: True if citations are found, False otherwise.
    """
    references = citation_pattern.search(text)
    return bool(references)

def discard_flags(text):
    """
    Checks if a text contains any citations using a regular expression pattern.

    Returns:
        bool: True if citations are found, False otherwise.
    """
    tokens = ['ORCID', 'DOI']
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

index_str_l = ['tablo', 'şekil', 'grafik', 'çizelge', 'table', 'figure', 'graph', 'chart']
index_heading_pattern = re.compile(r'dizini?$', re.IGNORECASE)
index_start_pattern = re.compile(r'^(' + '|'.join(index_str_l) + r')\s*\d+', re.IGNORECASE)
index_end_pattern = re.compile(r'\d+$', re.IGNORECASE)

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
    if index_start_pattern.search(current_line) and index_end_pattern.search(next_line):
        return True
    prev_line = prev_line.lower().replace('i̇', 'i').strip()
    if index_start_pattern.search(prev_line) and index_end_pattern.search(current_line):
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
        stats['is_turkish'] = is_turkish_content(line)
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

bibliography_keywords = ['Bibliyoğrafya', 'Bibliyografya', 'Bibliyog', 'Kaynakça', 'Kaynaklar', 'Kaynaklar/References']
bibliography_pattern = re.compile(r'^(' + '|'.join(bibliography_keywords) + r')\b', re.IGNORECASE)

def find_bibliography(df):
    # TODO: Handle the case where keywords are detected more than once.
    """
    Identifies the rows containing bibliography based on specific keywords.

    Returns:
        pd.DataFrame: The updated DataFrame with a column indicating the bibliography rows.
    """

    # Search for the keywords in the 'text_column'
    mask = df['line'].str.contains(r'^(' + '|'.join(bibliography_keywords) + r')', case=False, na=False, regex=True)

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
                break
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

        if (last_number - current_number <= 2) and gap <= 4:
            for j in range(last_index, i+1):
                df.loc[j, 'is_footnote'] = True

            last_number = current_number
            last_index = i

        else:
            if i != last_index + 1 and current_number != -1:
                last_number = current_number
                last_index = i

    return df

def convert_pdf_to_text(file):
    """
    Converts a PDF file to text, performs text analysis, and saves the results to a CSV file.

    The function reads the PDF file, computes line statistics, and identifies various line types
    such as footnotes, bibliography, etc. The processed results are then saved to a CSV file.

    Args:
        file (str): The path to the PDF file.
    """
    try:
        lines = [l.strip() for l in parser.from_file(file)['content'].split('\n') if l.strip()]
    except:
        print('Error during OCR:', file)
        return
    df = pd.DataFrame(compute_line_statistics(lines))
    df['final_number'] = df['final_number'].fillna(-1)

    # TODO: What if we perform this correction after dropping based on other conditions?
    df['is_turkish_corrected'] = df['is_turkish']
    df = correct_false_values(df, 'is_turkish')

    df = mark_footnotes(df)

    try:
        # Bibliography is not present in all pdfs.
        df = find_bibliography(df)
    except:
        df['is_bibliography'] = False

    index = df[(df['is_turkish_corrected'] == False)
                | ((df['digit_ratio'] >= 0.2) & (df['average_token_length'] < 4)) # usually table values
                | (df['digit_ratio'] == 1)                                        # page numbers
                | (df['has_email'])
                | (df['caption_type'] != 'Yok')
                | (df['is_footnote'])
                | (df['citation_format'])
                | (df['discard_flag'])
                | (df['affiliation_count'] > 0.15)
                | (df['occurrence'] > 2)
                | (df['is_bibliography'])
                | (df['is_footnote'])].index

    df.loc[index, 'drop'] = True
    df.to_csv(file.replace('pdf', 'csv'), encoding='utf-8', index=False)

    filtered_df = df.drop(index)
    with open(file.replace('pdf', 'txt'), 'w', encoding='utf-8') as f:
        f.write(' '.join(filtered_df['line'].tolist()))

def main():
    arg_parser = argparse.ArgumentParser(description='Extracts text from PDF files.')
    arg_parser.add_argument('-p', '--path', type=str, help='The path to the PDF folder or file.', required=True)
    arg_parser.add_argument('-n', '--num_threads', type=int, help='The number of threads to use.', default=4)
    args = arg_parser.parse_args()

    input_path = Path(args.path)
    if input_path.is_file() and input_path.name.endswith('.pdf'):
        input_files = [str(input_path)]
    elif input_path.is_dir():
        input_files = [str(f) for f in input_path.iterdir() if f.name.endswith('.pdf')]

    with Pool(args.num_threads) as pool:
        pool.map(convert_pdf_to_text, input_files)

if __name__ == '__main__':
    main()