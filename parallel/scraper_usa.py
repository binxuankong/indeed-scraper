#!/usr/bin/env python3
# coding: utf-8

import os
import argparse
import pandas as pd
import time
from scraping_functions import *

# Create the parser
parser = argparse.ArgumentParser()

# Add the arguments
parser.add_argument('Job', type=str, help='the Job to scrape')
parser.add_argument('State', type=str, help='the State to scrape in Abbreviation')

# Execute the parse_args() method
args = parser.parse_args()
print(args)

# Feedback max_jobs per base_url
what_job = args.Job.replace(" ", "+")
what_state = args.State
print(what_job)
base_url = f"https://www.indeed.com/jobs?q={what_job}&l={what_state}&fromage=7"
print(base_url)

job_num, max_pages = get_job_num(base_url)
counter = 0

for x in range(0, max_pages):
    output = []
    page_soup = get_page_soup(x, base_url)

    for job in page_soup.select(".tapItem"):
        infos = get_job_info(job)
        infos['Country'] = 'USA'
        infos['State'] = what_state
        output.append(infos)
        print("Successfuly Scrapped Job No {}/{}: {}".format(counter, job_num, infos['Job_Title']))
        # Wait
        time.sleep(random.uniform(1, 3))
    
    df = pd.DataFrame.from_dict(output)
    df = df.replace('\n', '', regex=True)
    path = '../output_usa/'
    new_path = os.path.join(path + what_job.replace("+", "_") + '.csv')
    if not os.path.isfile(new_path):
        df.to_csv(os.path.join(path + what_job.replace("+", "_") + '.csv'), header='column_names')
    # else it exists so append without writing the header
    else:
        df.to_csv(os.path.join(path+ what_job.replace("+", "_") +'.csv'), mode='a', header=False)
    # Wait
    time.sleep(random.uniform(3, 5))
