import re
import pandas as pd
from tika import parser
from langdetect import detect
from pathlib import Path
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

def check_email(line):
    """
    Checks if a line of text contains an email address.

    Returns:
        bool: True if an email address is found, False otherwise.
    """
    email_regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    return bool(re.search(email_regex, line))

def count_occurrence(lines, target_line):
    """
    Counts the number of occurrences of a target line in a list of lines.

    Returns:
        int: The number of occurrences.
    """
    return lines.count(target_line)

def find_caption_type(line):
    """
    Determines the type of a caption line (e.g., table, figure, etc.).

    Returns:
        str: The caption type if matched, 'Yok' (meaning 'None') otherwise.
    """
    for item in ['Tablo', 'Şekil', 'Fotoğraf', 'Figür', 'Resim', 'Plan', 'Nota', 'Çizelge', 'Grafik', 'Ek']:
        if re.match(fr"^{item}\s\d+[\.\:\-]", line): # \s\d+[\.\:]\s.+?\s\d+
            return item
    return 'Yok'

def capture_number_at_beginning(text):
    """
    Captures the number at the beginning of a text.

    Returns:
        int: The captured number, or None if no number is found.
    """
    match = re.match(r'^(\d+)', text)
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
    match = re.match(r'^(\d+)', text.strip()[::-1])
    if match:
        return int(match.group(1).strip()[::-1])
    else:
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

def capture_citations(text):
    """
    Checks if a text contains any citations using a regular expression pattern.

    Returns:
        bool: True if citations are found, False otherwise.
    """
    references = re.search('\(([A-Za-z–§¶\s\d\',:]+[\s,]\d{4}|\d+)\)', text, re.MULTILINE)
    if references:
        return True
    return False

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

def check_volume_number_format(text):
    """
    Checks if a text follows a specific volume and number format.

    Returns:
        bool: True if the format is matched, False otherwise.
    """
    pattern = r"vol\s*\d+\s*.+no\s\d+\s*.+p"
    tr_pattern = r"cilt\s*\d+\s*.+sayı\s\d+\s*.+s"

    match = re.search(pattern, text)
    tr_match = re.search(tr_pattern, text)
    return match is not None or tr_match is not None

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

def compute_line_statistics(lines):
    """
    Computes various statistics for each line in a list of lines.

    Returns:
        list: A list of dictionaries containing the line statistics.
    """
    statistics = []
    for line in lines:
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
        stats['occurrence'] = count_occurrence(lines, line)
        stats['caption_type'] = find_caption_type(line)
        stats['affiliation_count'] = compute_affiliation_ratio(line)
        stats['citation_format'] = check_volume_number_format(line)
        stats['discard_flag'] = discard_flags(line)
        stats['initial_number'] = capture_number_at_beginning(line)
        stats['final_number'] = capture_number_at_end(line)
        stats['has_citation'] = capture_citations(line)

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

def find_bibliography(df):
    # TODO: Handle the case where keywords are detected more than once.
    """
    Identifies the rows containing bibliography based on specific keywords.

    Returns:
        pd.DataFrame: The updated DataFrame with a column indicating the bibliography rows.
    """
    keywords = ['Bibliyoğrafya', 'Bibliyografya', 'Bibliyog', 'Kaynakça', 'Kaynaklar', 'Kaynaklar/References']

    # Search for the keywords in the 'text_column'
    mask = df['line'].str.contains(r'^(' + '|'.join(keywords) + r')', case=False, na=False, regex=True)

    # Get the index of the row(s) containing the keywords
    row_indices = df[mask].index
    print(row_indices)

    # If only one keyword is found
    if len(row_indices) == 1:
        bibliography_row_index = row_indices[0]
    # If more than one keyword is found, look for exact match or space after keyword, select the first match
    elif len(row_indices) > 1:
        matchFlag = False
        for i, row in df[mask].iterrows():
            match = re.search(r'^(' + '|'.join(keywords) + r')\b', row["line"], flags=re.IGNORECASE)
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

    print(bibliography_row_index, df.loc[bibliography_row_index, 'line'])

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
        # Bibliyograph is not presented in all pdfs.
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

arg_parser = argparse.ArgumentParser(description='Extracts text from PDF files.')
arg_parser.add_argument('-p', '--path', type=str, help='The path to the PDF folder.', required=True)
args = arg_parser.parse_args()

files = Path(args.path)
for f in files.iterdir():
    if f.name.endswith('.pdf'):
        convert_pdf_to_text(str(f))
