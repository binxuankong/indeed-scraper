#!/usr/bin/env python3
# coding: utf-8

import glob
import os
import pandas as pd
import numpy as np
import datetime
import string
import re
from datetime import datetime as dt
from sqlalchemy import create_engine
from secrets import settings

# Set up database and engine connection
DB_USER = ''
DB_PASS = ''
DB_HOST = ''
DB_PORT = ''
DATABASE = ''
connect_string = 'mysql+pymysql://{}:{}@{}:{}/{}'.format(DB_USER, DB_PASS, DB_HOST, DB_PORT, DATABASE)
engine = create_engine(connect_string)

# the path to your csv file directory
csvdir = '../output'
df_all = pd.DataFrame()
# get all the csv files 
csvfiles = glob.glob(os.path.join(csvdir, '*.csv'))
# loop through the files and read them in with pandas
for csvfile in csvfiles:
    what_job = os.path.split(os.path.splitext(csvfile)[0])[1]
    df = pd.read_csv(csvfile)
    df = df.drop_duplicates()
    # df.to_sql(name = what_job, con=engine, if_exists='append', index=False)
    df_all = df_all.append(df)

engine.dispose()

# Functions for SkillStreet
def get_org_and_det(df):
    companies = df['Company'].unique().tolist()
    org_id = df_org['id'].max() + 1
    org_det_id = df_org_det['id'].max() + 1
    org_list = []
    org_det_list = []
    df_no_org_det = df_org.loc[df_org['name'].isin(companies)]\
    .merge(df_org_det, left_on='id', right_on='organization_id', how='left')
    df_no_org_det = df_no_org_det.loc[df_no_org_det['id_y'].isna()]
    for c in companies:
        if not isinstance(c, str):
            continue
        if c in df_org['name'].tolist():
            if c in df_no_org_det['name'].tolist():
                this_org_id = df_org.loc[df_org['name'] == c]['id'].item()
                org_det = {
                    'id': org_det_id, 'status': False, 'created_user_id': -1, 'updated_user_id': -1,
                    'organization_id': this_org_id, 'created_date': datetime.datetime.now(),
                    'updated_date': datetime.datetime.now(),
                }
                org_det_list.append(org_det)
                org_det_id += 1
            continue
        organization_type_id = 2
        if 'university' in c.lower() or 'college' in c.lower():
            organization_type_id = 1
        org = {
            'id': org_id, 'status': False, 'activate': False, 'is_verified': False, 'name': c,
            'created_user_id': -1, 'updated_user_id': -1, 'organization_type_id': organization_type_id,
            'is_imported': True, 'created_date': datetime.datetime.now(), 'updated_date': datetime.datetime.now(),
        }
        org_det = {
            'id': org_det_id, 'status': False, 'created_user_id': -1, 'updated_user_id': -1,
            'organization_id': org_id, 'created_date': datetime.datetime.now(),
            'updated_date': datetime.datetime.now(),
        }
        org_list.append(org)
        org_id += 1
        org_det_list.append(org_det)
        org_det_id += 1
    
    df_org2 = pd.DataFrame.from_dict(org_list)
    df_org_det2 = pd.DataFrame.from_dict(org_det_list)
    return df_org2, df_org_det2

def get_country_org_salary_status(df):
    # Country
    df = df.merge(df_country[['id', 'name']], left_on='Country', right_on='name', how='left')\
        .drop(columns=['Country', 'Job_URL', 'name'])\
        .rename(columns={'id': 'country_id'})
    # Organization
    df = df.merge(df_org[['id', 'name']], left_on='Company', right_on='name', how='inner')\
        .merge(df_org_det[['id', 'organization_id']], left_on='id', right_on='organization_id', how='inner')\
        .drop(columns=['Company', 'id_x', 'name', 'organization_id'])\
        .rename(columns={'id_y': 'organization_details_id'})
    # Salary
    df[['salary_begin', 'salary_end']] = np.nan
    no_salary = df['Salary'].isna()
    df.loc[~no_salary, 'currency_id'] = df.loc[~no_salary, 'Salary'].apply(lambda x: extract_currency(x))
    df.loc[~no_salary] = extract_salary(df.loc[~no_salary])
    df = df.drop(columns=['Salary'])
    # Job Status
    df['Title_Keywords'] = df['Title_Keywords'].fillna('')
    df['job_status'] = 1
    df.loc[df['Title_Keywords'].str.contains('Part'), 'job_status'] = 2
    df.loc[df['Title_Keywords'].str.contains('Intern'), 'job_status'] = 3
    df = df.sort_values(by='Date_Posted')
    df = df.drop_duplicates()
    return df

def to_skillstreet_format(df, job_skill_list, job_other_list):
    df = df.drop_duplicates()
    df['Date_Posted'] = pd.to_datetime(df['Date_Posted'])
    global job_id
    job_list = []
    for _, row in df.iterrows():
        job_id += 1
        title_keywords = np.nan
        if len(row['Title_Keywords']) > 0:
            title_keywords = remove_quotes(row['Title_Keywords'])
        process_skills(job_id, row['Keywords_Present'], job_skill_list, job_other_list)
        job = {
            'id': job_id,
            'status': False,
            'description': row['Description'][:15000],
            'designation': row['Job_Title'],
            'job_status': row['job_status'],
            'location': row['Location'],
            'published_date': row['Date_Posted'].timestamp() * 1e3,
            'salary_begin': row['salary_begin'],
            'salary_end': row['salary_end'],
            'created_user_id': -1,
            'updated_user_id': -1,
            'country_id': row['country_id'],
            'organization_details_id': row['organization_details_id'],
            'published_by_id': -1,
            'is_smart_skill_required': False,
            'type': 1,
            'applicant_source': 1,
            'currency_id': row['currency_id'],
            'is_imported': True,
            'title_keywords': title_keywords,
            'created_date': datetime.datetime.now(),
            'updated_date': datetime.datetime.now(),
        }
        job_list.append(job)
    return pd.DataFrame.from_dict(job_list)

def extract_currency(salary):
    if 'RM' in salary:
        return 2
    elif 'Rp' in salary:
        return 6
    elif '$' in salary:
        return 8
    elif 'บาท' in salary:
        return 9
    elif 'PHP' in salary:
        return 10
    elif 'VNĐ' in salary:
        return 11

def extract_salary(df_job):
    df = df_job.copy()
    df[['salary_begin', 'salary_end']] = df['Salary'].str.split('-', 1, expand=True)
    # Set Upper NaN to Lower
    df.loc[df['salary_end'].isna(), 'salary_end'] = df.loc[df['salary_end'].isna(), 'salary_begin']
    # Convert to Numeric
    df['salary_begin'] = df['salary_begin'].map(lambda x: ''.join(filter(str.isdigit, x)))
    df['salary_end'] = df['salary_end'].map(lambda x: ''.join(filter(str.isdigit, x)))
    df['salary_begin'] = df['salary_begin'].map(lambda x: float(x.replace(',', '')))
    df['salary_end'] = df['salary_end'].map(lambda x: float(x.replace(',', '')))
    # Convert hours to month
    # Average 166.4 hours of work per month
    df.loc[df['Salary'].str.contains('hour'), 'salary_begin'] *= 166.4
    df.loc[df['Salary'].str.contains('hour'), 'salary_end'] *= 166.4
    # Convert days to month
    # Average 20.8 days of work per month
    df.loc[df['Salary'].str.contains('day'), 'salary_begin'] *= 20.8
    df.loc[df['Salary'].str.contains('day'), 'salary_end'] *= 20.8
    # Convert weeks to month
    # Average 4.3 weeks of work per month
    df.loc[df['Salary'].str.contains('week'), 'salary_begin'] *= 4.345
    df.loc[df['Salary'].str.contains('week'), 'salary_end'] *= 4.345
    # Convert years to month
    df.loc[df['Salary'].str.contains('year'), 'salary_begin'] /= 12
    df.loc[df['Salary'].str.contains('year'), 'salary_end'] /= 12
    return df

def remove_quotes(words):
    words = words.split(', ')
    words = [w.strip("'") for w in words]
    return ', '.join(words)

def get_skill_id(df, skill):
    if len(skill.split(' ')) > 1:
        df_temp = df.loc[df['name'].str.match(skill, case=False)]
    elif any(p in skill for p in string.punctuation):
        df_temp = df.loc[df['name'] == skill]
    else:
        df_temp = df.loc[df['name'].apply(lambda x: find_whole_word(skill.lower(), x.lower()))]
    if len(df_temp) > 1:
        return df_temp['id'].iloc[0]
    elif len(df_temp) == 1:
        return df_temp['id'].item()
    else:
        return None

def find_whole_word(search_string, input_string):
    raw_search_string = r"\b" + search_string + r"\b"
    match_output = re.search(raw_search_string, input_string)
    no_match_was_found = ( match_output is None )
    if no_match_was_found:
        return False
    else:
        return True

def process_skills(job_id, skills, job_skill_list, job_other_list):
    if not isinstance(skills, str):
        return
    for s in skills.split(', '):
        s = s.strip("'")
        if s == 'C':
            continue
        skill_id = get_skill_id(df_skill, s)
        if skill_id is not None:
            global job_skill_id
            job_skill_id += 1
            job_skill_list.append({'id': job_skill_id, 'status': True, 'created_user_id': -1, 'updated_user_id': -1,
                                   'job_project_posted_id': job_id, 'skill_id': skill_id,
                                   'created_date': dt.now(), 'updated_date': dt.now()})
        else:
            skill_id = get_skill_id(df_os2, s)
            global job_other_id
            job_other_id += 1
            if skill_id is None:
                global other_skill_id
                other_skill_id += 1
                df_os2.loc[len(df_os2)] = [other_skill_id, True, s, -1, -1, dt.now(), dt.now()]
                skill_id = other_skill_id
            job_other_list.append({'id': job_other_id, 'status': True, 'created_user_id': -1, 'updated_user_id': -1,
                                   'job_id': job_id, 'other_skill_id': skill_id, 'created_date': dt.now(),
                                   'updated_date': dt.now()})

# To Skillstreet
# Read existing data
engine = create_engine(settings['skillstreet_dev'])
df_country = pd.read_sql_query('select * from country', engine)
df_currency = pd.read_sql_query('select * from currency', engine)
df_org = pd.read_sql_query('select * from organization', engine)
df_org_det = pd.read_sql_query('select * from organization_details', engine)
df_job_skill = pd.read_sql_query('select * from job_required_skills', engine)
df_job_other = pd.read_sql_query('select * from job_other_skill', engine)
df_skill = pd.read_sql_query('select * from skill', engine)
df_other_skill = pd.read_sql_query('select * from other_skill', engine)
job_id = pd.read_sql_query('select max(id) from job_project_posted', engine)['max'].item()
# Get new organization and organization details
df_new_org, df_new_org_det = get_org_and_det(df)
df_org = df_org.append(df_new_org)
df_org_det = df_org_det.append(df_new_org_det)
# Get country id, organization id, salary and status
df_all = get_country_org_salary_status(df_all)
# Skills and other skills
df_os2 = df_other_skill.copy()
job_skill_id = df_job_skill['id'].max()
job_other_id = df_job_other['id'].max()
other_skill_id = df_other_skill['id'].max()
job_skill_list = []
job_other_list = []
# To SkillStreet format
df_final = to_skillstreet_format(df_all, job_skill_list, job_other_list)
df_job_skills = pd.DataFrame.from_dict(job_skill_list)
df_job_other_skills = pd.DataFrame.from_dict(job_other_list)
df_new_other_skills = pd.concat([df_os2, df_other_skill]).drop_duplicates(keep=False)
# To SQL
df_new_org.to_sql('organization', engine, if_exists='append', index=False)
df_new_org_det.to_sql('organization_details', engine, if_exists='append', index=False)
df_final.to_sql('job_project_posted', engine, if_exists='append', index=False)
df_new_other_skills.to_sql('other_skill', engine, if_exists='append', index=False)
df_job_skills.to_sql('job_required_skills', engine, if_exists='append', index=False)
df_job_other_skills.to_sql('job_other_skill', engine, if_exists='append', index=False)
engine.dispose()
