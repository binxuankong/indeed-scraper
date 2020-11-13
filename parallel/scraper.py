#!/usr/bin/env python3
# coding: utf-8

import os
import re
import csv
import sys
import urllib
import pymysql
import argparse
import numpy as np
import pandas as pd
import requests, json
import random
from collections import OrderedDict
from itertools import product, cycle
from lxml.html import fromstring
from bs4 import BeautifulSoup
from sqlalchemy import create_engine
from requests_html import HTMLSession
from datetime import datetime, timedelta
from skill_matching import skill_dict

import time
start_time = time.time()


# Create the parser
parser = argparse.ArgumentParser()

# Add the arguments

parser.add_argument('Job',
                       type=str,
                       help='the Job to scrape')
parser.add_argument('Country',
                       type=str,
                       help='the Country to scrape spelled-out')

# Execute the parse_args() method
args = parser.parse_args()
print(args)


default_parameters = {

        'skills_keywords':[line.strip() for line in open('../input/skills.txt', 'r')],
        'exclude_keywords':[line.strip() for line in open('../input/exclude.txt', 'r')],
        'title_keywords':[line.strip() for line in open('../input/level.txt', 'r')],
    }

headers_list = [
    # Firefox 77 Mac
     {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:77.0) Gecko/20100101 Firefox/77.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Referer": "https://www.google.com/",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    },
    # Firefox 77 Windows
    {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:77.0) Gecko/20100101 Firefox/77.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Referer": "https://www.google.com/",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    },
    # Chrome 83 Mac
    {
        "Connection": "keep-alive",
        "DNT": "1",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Dest": "document",
        "Referer": "https://www.google.com/",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8"
    },
    # Chrome 83 Windows
    {
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-User": "?1",
        "Sec-Fetch-Dest": "document",
        "Referer": "https://www.google.com/",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "en-US,en;q=0.9"
    }
]

# Create ordered dict from Headers above
ordered_headers_list = []
for headers in headers_list:
    h = OrderedDict()
    for header,value in headers.items():
        h[header]=value
    ordered_headers_list.append(h)

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
        return job.find('span', attrs={'class': 'salaryText'}).text
    except:
        return None

def extract_title(job):
    try:
        return job.find(class_='title').a['title']
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
        return job.find('span', attrs={'class': 'location'}).text
    except:
        return None

def extract_company(job_soup):
    try:
        return job.find('span', attrs={'class': 'company'}).text
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
        return job.find(id="jobDescriptionText").get_text()
    except:
        return str('No Description')

def extract_page_str(url, use_proxy=False):
    has_response = False
    if use_proxy:
        for i in range(10):
            proxy, is_elite = random_proxy()
            try:
                if is_elite:
                    html = requests.get(url, proxies=proxy)
                else:
                    headers = random.choice(headers_list)
                    html = requests.get(url, headers=headers, proxies=proxy)
                print("Succesful connection using proxy: {}".format(proxy))
                has_response = True
                break
            except:
                pass
    if not has_response:
        print("No proxy used")
        headers = random.choice(headers_list)
        html = requests.get(url, headers=headers, timeout=100)
    soup = BeautifulSoup(html.content, "html.parser")
    try:
        return soup.find("div", {"id": "searchCountPages"}).get_text()
    except:
        return str(['1','0'])

def fetch_country_url(country):
    if country=='Indonesia':
        return 'https://id.indeed.com/'
    elif country=='Malaysia':
        return 'https://www.indeed.com.my/'
    elif country=='Thailand':
        return 'https://th.indeed.com/'
    elif country=='Vietnam':
        return 'https://vn.indeed.com/'
    elif country=='Philippines':
        return 'https://www.indeed.com.ph/'
    elif country=='Singapore':
        return 'https://www.indeed.com.sg/'
    elif country=='Australia':
        return 'https://au.indeed.com/'
    elif country=='Canada':
        return 'https://ca.indeed.com/'
    elif country=='New Zealand':
        return  'https://nz.indeed.com/'
    elif country=='United Kingdom':
        return 'https://www.indeed.co.uk/'


 # Feedback max_jobs per base_url

country_url = fetch_country_url(args.Country)
print(country_url)

what_job = args.Job.replace(" ","+")
print(what_job)
base_url = f"{country_url}jobs?q={what_job}&fromage=7"
print(base_url)

# proxies = get_proxies()
# proxy_pool = cycle(proxies)

jobs_num_str = extract_page_str(base_url, use_proxy=True)
job_num =  re.findall(r'(?<!,)\b(\d{1,3}(?:,\d{3})*)\b(?!,)', jobs_num_str)
job_num = int(re.sub(',','', job_num[-1]))

print("No. of Jobs to Scrape:", job_num)
if (job_num==0):
    max_pages = 0
if (job_num>1000):
    max_pages = 100
else:
    max_pages = int(np.ceil(job_num/10))
print("No. of Pages to Scrape:", max_pages)

output = []
counter = 0

# Loop over max pages
for x in range(0, max_pages):
    if(x==0):
        page_append = ""
    else:
        page_append = "&start=" + str(x*10)

    headers = random.choice(headers_list)
    current_page = requests.get(base_url+page_append, headers=headers)
    page_soup = BeautifulSoup(current_page.content,"html.parser")

    for job in page_soup.select(".jobsearch-SerpJobCard"):
        output = []
        job_url = job.find(class_='title').a['href']

        session = HTMLSession()

        # Correct for truncated URLs
        job_url = country_url + job_url[1:] if job_url.startswith("/") else job_url
        response = session.get(job_url)

        # Get only english headers
        headers = {'Accept-Language': 'en-US,en;q=0.8'}
        # job_page = requests.get(job_url, headers , timeout=100 )
        job_soup = BeautifulSoup(response.content, 'html.parser')

        # Give URL after redirect (ads/analytics etc.)
        title = extract_title(job)
        company = extract_company(job)
        location = extract_location(job)
        metadata = extract_metadata(job)
        date = extract_date(job)
        ID = extract_id(job)
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
        for index,keyword in enumerate(keywords):
            if keyword in description:
                if keyword in skill_dict.keys():
                    keyword = skill_dict[keyword]
                keywords_present.append(keyword)
        keywords_present = list(set(keywords_present))

        # Check for title keywords
        for index,keyword in enumerate(title_keywords):
            if keyword in title:
                title_keywords_present.append(keyword)

        keywords_present = str(keywords_present)[1:-1]
        title_keywords_present = str(title_keywords_present)[1:-1]


        output.append([ID, title, company, salary, args.Country, 'Not Applicable', location, metadata, date, description, job_url, keywords_present,title_keywords_present])

        df = pd.DataFrame(
                    output, columns=['Job_ID', 'Job_Title', 'Company', 'Salary' , 'Country', 'State',  'Location' ,
                                        'Metadata', 'Date_Posted','Description','Job_URL','Keywords_Present',
                                        'Title_Keywords'])

        df = df.replace('\n', '', regex=True)
        path = '../output/'

        new_path = os.path.join(path + what_job.replace("+", "_") + '.csv')
        if not os.path.isfile(new_path):
            df.to_csv(os.path.join(path + what_job.replace("+", "_") + '.csv'), header='column_names')
        else:
            df.to_csv(os.path.join(path+ what_job.replace("+", "_") +'.csv'), mode='a', header=False)

        counter += 1
        print("Successfuly Scraped SEA: {} {}\tJob No: {}/{}".format(what_job, args.Country, counter, job_num))

elapsed_time = time.time() - start_time
