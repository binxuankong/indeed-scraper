import requests
import random
import re
import numpy as np
from bs4 import BeautifulSoup
from requests_html import HTMLSession
from lxml.html import fromstring
from datetime import datetime, timedelta
from configs import headers_list, custom_cookie
from skill_matching import skill_dict

default_parameters = {
        'skills_keywords':[line.strip() for line in open('../input/skills.txt', 'r')],
        'exclude_keywords':[line.strip() for line in open('../input/exclude.txt', 'r')],
        'title_keywords':[line.strip() for line in open('../input/level.txt', 'r')],
    }

def get_job_num(base_url, use_cookie=False):
    jobs_num_str = extract_page_str(base_url, use_cookie)
    job_num =  re.findall(r'(?<!,)\b(\d{1,3}(?:,\d{3})*)\b(?!,)', jobs_num_str)
    job_num = int(re.sub(',','', job_num[-1]))
    print("No. of Jobs to Scrape:", job_num)
    if job_num == 0:
        max_pages = 0
    if job_num > 1000:
        max_pages = 100
    else:
        max_pages = int(np.ceil(job_num/10))
    print("No. of Pages to Scrape:", max_pages)
    return job_num, max_pages

def get_page_soup(x, base_url, use_cookie=False):
    if x == 0:
        page_append = ""
    else:
        page_append = "&start=" + str(x*10)
    headers = random_headers(use_cookie)
    current_page = requests.get(base_url+page_append, headers=headers, timeout=100)
    page_soup = BeautifulSoup(current_page.content, "html.parser")
    return page_soup

def get_job_info(job):
    session = HTMLSession()
    job_url = f"https://www.indeed.com" + job['href']
    response = session.get(job_url)
    # Get only english headers
    headers = {'Accept-Language': 'en-US,en;q=0.8'}
    job_soup = BeautifulSoup(response.content, 'html.parser')
    # Get info
    title = extract_title(job)
    company = extract_company(job)
    location = extract_location(job)
    metadata = extract_metadata(job)
    date = extract_date(job)
    _id = extract_id(job)
    salary = extract_salary(job)
    # Get description, rating and present keywords
    description = extract_description_txt(job_soup)
    keywords = default_parameters['skills_keywords']
    title_keywords = default_parameters['title_keywords']
    exclude_keywords = default_parameters['exclude_keywords']
    total_keywords = len(keywords) + len(title_keywords)
    keywords_present = []
    title_keywords_present = []
    # Check for keyword
    for _, keyword in enumerate(keywords):
        if keyword in description:
            if keyword in skill_dict.keys():
                keyword = skill_dict[keyword]
            keywords_present.append(keyword)
    keywords_present = list(set(keywords_present))
    # Check for title keywords
    for _, keyword in enumerate(title_keywords):
        if keyword in title:
            title_keywords_present.append(keyword)
    keywords_present = str(keywords_present)[1:-1]
    title_keywords_present = str(title_keywords_present)[1:-1]
    return {'Job_ID': _id,
            'Job_Title': title,
            'Company': company,
            'Salary': salary,
            'Location': location,
            'Metadata': metadata,
            'Date_Posted': date,
            'Description': description,
            'Job_URL': job_url,
            'Keywords_Present': keywords_present,
            'Title_Keywords': title_keywords_present
    }

def random_proxy():
    url_free_proxy = 'https://sslproxies.org/'
    response = requests.get(url_free_proxy)
    parser = fromstring(response.text)
    proxies = set()
    for i in parser.xpath('//tbody/tr')[:20]:
        if i.xpath('.//td[7][contains(text(),"yes")]'):
            is_elite = False
            proxy = ":".join([i.xpath('.//td[1]/text()')[0], i.xpath('.//td[2]/text()')[0]])
            if i.xpath('.//td[5][contains(text(),"elite")]'):
                is_elite = True
            proxies.add((proxy, is_elite))
    proxy, is_elite = random.choice(list(proxies))
    return {'https': proxy}, is_elite

def get_proxies():
    # url_free_proxy = 'https://free-proxy-list.net/'
    url_free_proxy = 'https://sslproxies.org/'
    response = requests.get(url_free_proxy)
    parser = fromstring(response.text)
    proxies = set()
    for i in parser.xpath('//tbody/tr'):
        if i.xpath('.//td[7][contains(text(),"yes")]'):
            proxy = ":".join([i.xpath('.//td[1]/text()')[0], i.xpath('.//td[2]/text()')[0]])
            proxies.add(proxy)
    return proxies

def random_headers(use_cookie=False):
    headers = random.choice(headers_list)
    if use_cookie:
        headers['Cookie'] = custom_cookie
    return headers

def return_days_posted(job_posted):
        days = job_posted.split()[0]
        if days == 'Just':
            return 0
        elif days == 'Today':
            return 0
        elif days == '30+':
            return 31
        else:
            return days

def extract_salary(job):
    try:
        return job.find('span', attrs={'class': 'salary-snippet'}).text
    except:
        return None

def extract_title(job):
    try:
        return job.find('h2', attrs={'class': 'jobTitle'}).find_all('span')[-1].text
    except:
        return None
    
def extract_age(job):
    try:
        date_posted = job.find('span', attrs={'class': 'date'}).text
        ndays = return_days_posted(date_posted)
        return int(ndays)
    except:
        return None

def extract_date(job):
    try:
        date_posted = job.find('span', attrs={'class': 'date'}).text
        ndays = return_days_posted(date_posted)
        date = datetime.now() - timedelta(days=int(ndays))
        date = date.date()
        return date
    except:
        return None

def extract_location(job):
    try:
        location = job.find('div', attrs={'class': 'companyLocation'})
        span_text = ''.join([s.text for s in location.find_all('span')])
        if len(span_text) > 0:
            return location.text[:-len(span_text)].strip()
        else:
            return location.text.strip()
    except:
        return None

def extract_company(job):
    try:
        return job.find('span', attrs={'class': 'companyName'}).text
    except:
        return None

def extract_metadata(job):
    try:
        return job.find('span', attrs= {'class':'jobsearch-JobMetadataHeader-iconLabel'})
    except:
        return None

def extract_id(job):
    try:
        return job.get('data-jk', None)
    except:
        return None

def extract_description_txt(job):
    try:
        return job.find(id="jobDescriptionText").get_text(separator="\n")
    except:
        return str('No Description')

def extract_page_str(url, use_cookie=False):
    headers = random_headers(use_cookie)
    html = requests.get(url, headers=headers, timeout=100)
    soup = BeautifulSoup(html.content,"html.parser")
    try:
        return soup.find("div", {"id": "searchCountPages"}).get_text()
    except:
        return str(['1','0'])

def fetch_country_url(country):
    if country == 'Indonesia':
        return 'https://id.indeed.com/'
    elif country == 'Malaysia':
        return 'https://www.indeed.com.my/'
    elif country == 'Thailand':
        return 'https://th.indeed.com/'
    elif country == 'Vietnam':
        return 'https://vn.indeed.com/'
    elif country == 'Philippines':
        return 'https://www.indeed.com.ph/'
    elif country == 'Singapore':
        return 'https://www.indeed.com.sg/'
    elif country == 'Australia':
        return 'https://au.indeed.com/'
    elif country == 'Canada':
        return 'https://ca.indeed.com/'
    elif country == 'New Zealand':
        return  'https://nz.indeed.com/'
    elif country == 'United Kingdom':
        return 'https://www.indeed.co.uk/'
