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
from itertools import product
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
parser.add_argument('State',
                       type=str,
                       help='the State to scrape in Abbreviation')

# Execute the parse_args() method
args = parser.parse_args()
print(args)

default_parameters = {

        'skills_keywords':[line.strip() for line in open('../input/skills.txt', 'r')],
        'exclude_keywords':[line.strip() for line in open('../input/exclude.txt', 'r')],
        'title_keywords':[line.strip() for line in open('../input/level.txt', 'r')],
    }

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
        return job_soup.find(class_="icl-u-lg-mr--sm").get_text()
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

def extract_page_str(url):
    html = requests.get(url, timeout=100)
    soup = BeautifulSoup(html.content,"html.parser")
    try:
        return soup.find("div", {"id": "searchCountPages"}).get_text()
    except:
        return str(['1','0'])

# Feedback max_jobs per base_url
what_job = args.Job.replace(" ","+")
what_state = args.State
print(what_job)
base_url = f"https://www.indeed.com/jobs?q={what_job}&l={what_state}&fromage=7"
print(base_url)

jobs_num_str = extract_page_str(base_url)
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

# Loop over max pages
for x in range(0, max_pages):
    if(x==0):
        page_append = ""
    else:
        page_append = "&start=" + str(x*10)

    current_page = requests.get(base_url+page_append)
    page_soup = BeautifulSoup(current_page.content,"html.parser")

    for job in page_soup.select(".jobsearch-SerpJobCard"):


        job_url = job.find(class_='title').a['href']
        session = HTMLSession()
        # Correct for truncated URLs
        response = session.get(f"https://www.indeed.com/" + job_url if (job_url.startswith("/")) else job_url)

        # Correct for truncated URLs
        job_url = f"https://www.indeed.com/" + job_url if (job_url.startswith("/")) else job_url

        # Get only english headers
        headers = {'Accept-Language': 'en-US,en;q=0.8'}
        job_page = requests.get(job_url, headers , timeout=100 )
        job_soup = BeautifulSoup(response.content, 'html.parser')

        # Give URL after redirect (ads/analytics etc.)
        title = extract_title(job)
        company = extract_company(job_soup)
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


        output.append([ID, title, company, salary, 'USA', what_state, location, metadata, date, description, job_url, keywords_present,title_keywords_present])

        df = pd.DataFrame(
                    output, columns=['Job_ID', 'Job_Title', 'Company', 'Salary' , 'Country', 'State',  'Location' ,
                                        'Metadata', 'Date_Posted','Description','Job_URL','Keywords_Present',
                                        'Title_Keywords'])

        df = df.replace('\n', '', regex=True)
        path = '../output_usa/'

        new_path = os.path.join(path + what_job.replace("+", "_") + '.csv')
        if not os.path.isfile(new_path):
            df.to_csv(os.path.join(path + what_job.replace("+", "_") + '.csv'), header='column_names')

        # else it exists so append without writing the header
        else:
            df.to_csv(os.path.join(path+ what_job.replace("+", "_") +'.csv'), mode='a', header=False)


        print("Successfuly Scrapped USA:",  what_job, what_state)

elapsed_time = time.time() - start_time
