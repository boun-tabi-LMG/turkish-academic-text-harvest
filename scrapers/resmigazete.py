import time 
import requests
from pathlib import Path
def download_files_with_id_pattern(start_id, end_id):
    """
    Downloads files from the URL pattern "https://www.resmigazete.gov.tr/arsiv/{ID}.pdf" where ID is between start_id and end_id.

    Args:
    - start_id (int): The starting ID value.
    - end_id (int): The ending ID value.

    Returns:
    None
    """
    for ID in range(start_id, end_id + 1):
        if Path(f"pdf/{ID}.pdf").is_file():
            continue
        time.sleep(5)
        url = f"https://www.resmigazete.gov.tr/arsiv/{ID}.pdf"
        try:
            response = requests.get(url)
        
            if response.status_code == 200:
                with open(f"pdf/{ID}.pdf", "wb") as file:
                    file.write(response.content)
                print(f"File {ID}.pdf downloaded successfully.")
            else:
                print(f"Failed to download file {ID}.pdf. Response: {response}")
        except:
            print('Failed to download file {ID}.pdf')

def download_pdf_files_with_date_pattern(start_year, end_year, start_month, end_month, start_day, end_day):
    """
    Downloads files from the URL pattern "https://resmigazete.gov.tr/eskiler/YYYY/MM/YYYYMMDD.pdf".

    Args:
    - start_year (int): The starting year.
    - end_year (int): The ending year.
    - start_month (int): The starting month.
    - end_month (int): The ending month.
    - start_day (int): The starting day.
    - end_day (int): The ending day.

    Returns:
    None
    """
    for year in range(start_year, end_year + 1):
        for month in range(start_month, end_month + 1):
            for day in range(start_day, end_day + 1):
                date = f"{year:04d}{month:02d}{day:02d}"
                if Path(f"pdf/{date}.pdf").is_file():
                    continue
                if year == 2000 and month < 6: 
                    continue
                url = f"https://resmigazete.gov.tr/eskiler/{year}/{month:02d}/{date}.pdf"
                time.sleep(3)
                try:
                    response = requests.get(url)
                
                    if response.status_code == 200:
                        with open(f"pdf/{date}.pdf", "wb") as file:
                            file.write(response.content)
                        print(f"File {date}.pdf downloaded successfully.")
                    else:
                        print(f"Failed to download file {date}.pdf. Response: {response}")
                except:
                    print('Failed to download file {date}.pdf')


def download_html_files_with_date_pattern(start_year, end_year, start_month, end_month, start_day, end_day):
    """
    Downloads files from the URL pattern "https://resmigazete.gov.tr/eskiler/YYYY/MM/YYYYMMDD.htm"

    Args:
    - start_year (int): The starting year.
    - end_year (int): The ending year.
    - start_month (int): The starting month.
    - end_month (int): The ending month.
    - start_day (int): The starting day.
    - end_day (int): The ending day.

    Returns:
    None
    """
    for year in range(start_year, end_year + 1):
        for month in range(start_month, end_month + 1):
            for day in range(start_day, end_day + 1):
                date = f"{year:04d}{month:02d}{day:02d}"
                base_url = f"https://resmigazete.gov.tr/eskiler/{year}/{month:02d}/{date}.htm"
                time.sleep(1)
                try:
                #if 1: 
                    response = requests.get(base_url)
                    if response.status_code == 200:
                        Path(f"htm/{date}/").mkdir(exist_ok=True, parents=True)
                        with open(f"htm/{date}/{date}.htm", "wb") as file:
                            file.write(response.content)
                            print(f"File {date} downloaded successfully.")

                        soup = BeautifulSoup(response.content, 'html.parser')
                        links = soup.find_all('a')
                        for link in links: 
                            url = link.get('href')
                            print(url)
                            if url is None or url.startswith('#'):
                                continue
                            #elif not url.split('/')[-1].startswith(date): 
                            #    continue
                            time.sleep(1)
                            #if 1: 
                            try:
                                #if date not in url: 
                                #    url = f'{base_url.replace(".htm", "")}{url}'
                                print(f"https://resmigazete.gov.tr/eskiler/{year}/{month:02d}/{url}")
                                response = requests.get(f"https://resmigazete.gov.tr/eskiler/{year}/{month:02d}/{url}")
                                if response.status_code == 200:
                                     with open(f"htm/{date}/{url.split('/')[-1]}", "wb") as file:
                                        file.write(response.content)
                                        print(f"File {url} downloaded successfully.")
                                else: 
                                    print(response.status_code)
                            except: 
                                print(f'Failed to dowload file {url}')
                    else:
                        print(f"Failed to download file {date}. Response: {response}")
                except:
                    print(f'Failed to download file {date}')

# Download files with ID pattern
start_id = 1054
end_id = 24095
download_files_with_id_pattern(start_id, end_id)

# Download files with date pattern
start_year = 2000
end_year = 2023
start_month = 1
end_month = 12
start_day = 1
end_day = 31

download_pdf_files_with_date_pattern(start_year, end_year, start_month, end_month, start_day, end_day)

download_html_files_with_date_pattern(start_year, end_year, start_month, end_month, start_day, end_day)