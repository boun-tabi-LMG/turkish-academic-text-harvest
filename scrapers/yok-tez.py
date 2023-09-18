import requests
import re
import logging
import os
import json
from bs4 import BeautifulSoup

THIS_DIR = os.path.dirname(os.path.abspath(__file__))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_l_from_br(text):
    while '  ' in text:
        text = text.replace('  ', ' ')
    l = [i.strip() for i in text.split('<br/>')]
    return l


def fetch_pdf_files(start_id=1, end_id=798285, get_pdfs=True, get_mds=True, get_sources=False):
    """
    Fetches PDF files from a website using a search and download process.

    This function sends requests to a website, searches for PDF files, and downloads them
    based on a given range of TezNo values.

    Args:
    - till (int): The upper limit (inclusive) of the TezNo range. Defaults to 798285.

    Returns:
    None
    """

    if get_pdfs:
        pdf_dir = os.path.join(THIS_DIR, 'pdfs')
        if not os.path.exists(pdf_dir):
            os.makedirs(pdf_dir)
    if get_mds:
        md_path = os.path.join(THIS_DIR, 'md.json')
        if not os.path.exists(md_path):
            with open(md_path, 'w') as f:
                json.dump({}, f, ensure_ascii=False, indent=4)
        with open(md_path, 'r') as f:
            md_d = json.load(f)
    if get_sources:
        source_dir = os.path.join(THIS_DIR, 'sources')
        if not os.path.exists(source_dir):
            os.makedirs(source_dir)

    session = requests.Session()
    session.headers.update(
        {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})

    search_tez_url = 'https://tez.yok.gov.tr/UlusalTezMerkezi/SearchTez'
    tez_detay_url = 'https://tez.yok.gov.tr/UlusalTezMerkezi/tezDetay.jsp?id={id_t}'
    download_url = 'https://tez.yok.gov.tr/UlusalTezMerkezi/TezGoster?key={key_t}'

    payload_str = 'uniad=&Universite=0&Tur=0&yil1=0&yil2=0&ensad=&Enstitu=0&izin=0&abdad=&ABD=0&Durum=3&TezAd=&bilim=&BilimDali=0&Dil=1&AdSoyad=&Konu=&EnstituGrubu=&DanismanAdSoyad=&Dizin=&Metin=&islem=2&Bolum=0&-find=++Bul++'
    payload_d = {i: j for i, j in [
        i.split('=') for i in payload_str.split('&')]}

    id_pattern = re.compile('onclick=tezDetay\(\'(.*?)\',')
    pdf_pattern = re.compile('<a href="TezGoster\?key=(.*?)"')

    for thesis_id in range(start_id, end_id + 1):
        form_data = payload_d.copy()
        form_data['TezNo'] = thesis_id

        try:
            # Send search request
            search_tez_response = session.post(search_tez_url, data=form_data)
            search_tez_response.raise_for_status()

            text = search_tez_response.text

            # Extract tezDetay id
            id_search = id_pattern.search(text)
            if id_search:
                id_t = id_search.group(1)

                # Send tezDetay request
                tez_detay_response = session.get(
                    tez_detay_url.format(id_t=id_t))
                tez_detay_response.raise_for_status()

                text = tez_detay_response.text

                if get_sources:
                    with open(os.path.join(source_dir, f'{thesis_id}.html'), 'w', encoding='utf-8') as f:
                        f.write(text)
                        logger.info(f'{thesis_id}.html saved')

                if get_mds:
                    soup = BeautifulSoup(text, 'html.parser')
                    md_l = soup.find_all('td', {'valign': 'top'})
                    d_t = {}
                    if len(md_l) == 4:
                        kunye = md_l[2]
                        for i, child in enumerate(kunye.children):
                            child_str = str(child).strip()
                            if i == 0:
                                d_t['title'] = child_str
                            elif i == 2:
                                d_t['author'] = child_str.split(':')[1].strip()
                            elif i == 4:
                                d_t['advisor'] = child_str.split(':')[
                                    1].strip()
                            elif i == 6:
                                d_t['university'] = child_str.split(':')[
                                    1].strip()
                            elif i == 8:
                                d_t['topic'] = child_str.split(':')[1].strip()
                            elif i == 10:
                                d_t['index'] = child_str.split(':')[1].strip()
                        status = md_l[3]
                        for i, child in enumerate(status.children):
                            child_str = str(child).strip()
                            if i == 2:
                                d_t['type'] = child_str
                            elif i == 6:
                                d_t['year'] = child_str
                            elif i == 8:
                                d_t['page_count'] = child_str
                        md_d[str(thesis_id)] = d_t
                        print(str(thesis_id), len(md_d))

                if get_pdfs:
                    # Extract PDF key
                    pdf_search = pdf_pattern.search(text)
                    if pdf_search:
                        key_t = pdf_search.group(1)

                        # Send download request
                        download_response = session.get(
                            download_url.format(key_t=key_t))
                        download_response.raise_for_status()

                        # Save PDF file
                        with open(os.path.join(pdf_dir, f'{thesis_id}.pdf'), 'wb') as f:
                            f.write(download_response.content)
                            logger.info(f'{thesis_id}.pdf saved')

            with open(md_path, 'w') as f:
                json.dump(md_d, f, ensure_ascii=False, indent=4)

        except (requests.RequestException, IOError) as e:
            logger.error(
                f'Error occurred while fetching PDF for TezNo {thesis_id}: {str(e)}')

        except Exception as e:
            logger.error(
                f'Unexpected error occurred while fetching PDF for TezNo {thesis_id}: {str(e)}')


# Call the function to start fetching PDF files
fetch_pdf_files(get_pdfs=False, get_mds=True, get_sources=False)
