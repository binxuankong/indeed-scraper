#!/usr/bin/env python3
# coding: utf-8

import os
import argparse
import pandas as pd
import time
from collections import OrderedDict
from scraping_functions import *

# Create the parser
parser = argparse.ArgumentParser()

# Add the arguments
parser.add_argument('Job', type=str, help='the Job to scrape')
parser.add_argument('Country', type=str, help='the Country to scrape spelled-out')

# Execute the parse_args() method
args = parser.parse_args()
print(args)

# Create ordered dict from Headers above
ordered_headers_list = []
for headers in headers_list:
    h = OrderedDict()
    for header,value in headers.items():
        h[header]=value
    ordered_headers_list.append(h)

# Feedback max_jobs per base_url
country_url = fetch_country_url(args.Country)
print(country_url)

what_job = args.Job.replace(" ", "+")
print(what_job)
base_url = f"{country_url}jobs?q=\"{what_job}\"&fromage=7"
print(base_url)

use_cookie = False

job_num, max_pages = get_job_num(base_url, use_cookie)
counter = 0

for x in range(0, max_pages):
    output = []
    page_soup = get_page_soup(x, base_url, use_cookie)

    for job in page_soup.select(".tapItem"):
        infos = get_job_info(job)
        infos['Country'] = args.Country
        # infos['State'] = 'Not Applicable'
        output.append(infos)
        counter += 1
        print("Successfuly Scrapped Job No {}/{}: {}".format(counter, job_num, infos['Job_Title']))
        # Wait
        time.sleep(random.uniform(1, 3))
    
    df = pd.DataFrame.from_dict(output)
    df = df.replace('\n', '', regex=True)
    path = '../output/'
    new_path = os.path.join(path + what_job.replace("+", "_") + '.csv')
    if not os.path.isfile(new_path):
        df.to_csv(os.path.join(path + what_job.replace("+", "_") + '.csv'), header='column_names')
    # else it exists so append without writing the header
    else:
        df.to_csv(os.path.join(path+ what_job.replace("+", "_") +'.csv'), mode='a', header=False)
    # Wait
    time.sleep(random.uniform(3, 5))
