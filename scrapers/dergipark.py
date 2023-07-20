import requests
import pandas as pd
from bs4 import BeautifulSoup
from pathlib import Path 
import logging
import json
import time

logging.basicConfig(level=logging.INFO)

def get_url(url): 
    """
    Sends a GET request to the specified URL and handles retries for certain HTTP status codes.

    Args:
    - url (str): The URL to send the request to.

    Returns:
    - response (requests.Response): The response object obtained from the request.
    """

    session = requests.Session()
    retry_strategy = requests.adapters.Retry(total=5, backoff_factor=0.1, status_forcelist=[500, 502, 503, 504])
    adapter = requests.adapters.HTTPAdapter(max_retries=retry_strategy)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    
    return session.get(url, timeout=10)
    
    
def download_pdf(url, destination_path):
    """
    Downloads a PDF file from the specified URL and saves it to the destination path.

    Args:
    - url (str): The URL of the PDF file to download.
    - destination_path (str): The path where the downloaded PDF file should be saved.

    Returns:
    None
    """
    
    response = get_url(url)
    
    if response.status_code == 200:
        with open(destination_path, 'wb') as file:
            file.write(response.content)
        
        logging.info('PDF downloaded successfully.')
    else:
        logging.error(f'Failed to download the PDF from {url}. Response: {response}')


def download_article(journal_code, issue_number, article_no):
    """
    Downloads an article's PDF file and saves its metadata as JSON.

    Args:
    - journal_code (str): The code of the journal.
    - issue_number (str): The issue number.
    - article_no (str): The article number.

    Returns:
    - article_data (dict): A dictionary containing the extracted article metadata.
    """

    url = f'https://dergipark.org.tr/en/pub/{journal_code}/issue/{issue_number}/{article_no}'
    response = get_url(url)
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        article_tr = soup.find(id='article_tr')

        if article_tr is None: 
            logging.error(f'Failed to retrieve article {journal_code} {issue_number} {article_no}: tr element not found')
            return {}

        article_data = {}

        for class_name in classes:
            element_value = article_tr.find(class_=class_name)
            article_data[class_name] = element_value.text.strip() if element_value else ''

        download_link = ''

        for link in soup.find_all('a', href=lambda href: href and 'download/article-file/' in href):
            download_link = link.get('href')
            break

        if download_link:
            download_pdf(f'https://dergipark.org.tr{download_link}', f'pdf/{journal_code}_{issue_number}_{article_no}.pdf')

            with open(f'metadata/{journal_code}_{issue_number}_{article_no}.json', 'w', encoding='utf-8') as f:
                json.dump(article_data, f)

        return article_data

    else:
        logging.error(f'Failed to retrieve article {journal_code} {issue_number} {article_no}')
        return {}


def retrieve_articles(journal_code, issue_number):
    """
    Retrieves the list of articles for a given journal and issue.

    Args:
    - journal_code (str): The code of the journal.
    - issue_number (str): The issue number.

    Returns:
    - article_list (list): A list of article links for the specified journal and issue.
    """

    url = f'https://dergipark.org.tr/en/pub/{journal_code}/issue/{issue_number}'
    retries = 5
    
    while retries > 0:
        response = get_url(url)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            article_elements = soup.find_all('a', href=lambda href: href and f'{journal_code}/issue/{issue_number}' in href)
    
            article_list = [element['href'] for element in article_elements]
            return article_list
    
        else:
            logging.error(f'Failed to retrieve articles from journal {journal_code} {issue_number}. Retries left: {retries}')
            retries -= 1
            time.sleep(30)
    
    return []


def get_issues(journal_code):
    """
    Retrieves the list of issues for a given journal.

    Args:
    - journal_code (str): The code of the journal.

    Returns:
    - issue_list (list): A list of issue links for the specified journal.
    """

    url = f'https://dergipark.org.tr/en/pub/{journal_code}/archive'
    retries = 5
    
    while retries > 0:
        response = get_url(url)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            issue_elements = soup.find_all('a', href=lambda href: href and f'dergipark.org.tr/en/pub/{journal_code}/issue/' in href)
    
            issue_list = [element['href'] for element in issue_elements]
            return issue_list
    
        else:
            logging.error(f'Failed to retrieve journal issues {journal_code}. Retries left: {retries}')
            retries -= 1
            time.sleep(30)
    
    return []


def get_journal_list(page_no):
    """
    Retrieves the list of journals from a specific page.

    Args:
    - page_no (int): The page number to retrieve the journal list from.

    Returns:
    - journal_list (list): A list of journal links from the specified page.
    """

    url = f'https://dergipark.org.tr/en/search{page_no}?aggs%5BmandatoryLang%5D%5B11%5D=tr&section=journal&q='
    response = get_url(url)
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        journal_elements = soup.find_all('a', href=lambda href: href and 'https://dergipark.org.tr/en/pub/' in href)

        journal_list = [element['href'] for element in journal_elements]
        return journal_list

    else:
        logging.error(f'Failed to retrieve page {page_no}')
        return []


# Retrieve the list of journals and save it to a CSV file
all_journals = []
for page in [''] + [f'/{i}' for i in range(2, 83)]:
    all_journals.extend(get_journal_list(page))
pd.DataFrame(list(set(all_journals))).to_csv('journals.csv', index=False)

# Load the journal list from the CSV file
df = pd.read_csv('journals.csv', header=None, names=['journals'])
all_journals = df['journals'].tolist()

path_meta = Path('metadata')
path_pdf = Path('pdf')

for journal_link in all_journals:
    journal_code = journal_link.split('/')[-1].strip()
    issue_list = get_issues(journal_code)

    for issue_link in issue_list:
        issue_number = issue_link.split('/')[-1].strip()
        article_list = retrieve_articles(journal_code, issue_number)

        for article_link in article_list:
            article_no = article_link.split('/')[-1].strip()
            meta_file = path_meta / f'{journal_code}_{issue_number}_{article_no}.json' 
            pdf_file = path_pdf / f'{journal_code}_{issue_number}_{article_no}.pdf'
            
            if meta_file.is_file() and pdf_file.is_file():
                continue
            
            try: 
                download_article(journal_code, issue_number, article_no)
            except requests.ConnectionError:
                time.sleep(30)

