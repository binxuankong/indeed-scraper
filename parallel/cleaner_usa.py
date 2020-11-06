#!/usr/bin/env python3
# coding: utf-8

import glob
import os
import pandas as pd
from sqlalchemy import create_engine

# Set up database and engine connection
DB_USER = ''
DB_PASS = ''
DB_HOST = ''
DB_PORT = ''
DATABASE = ''
connect_string = 'mysql+pymysql://{}:{}@{}:{}/{}'.format(DB_USER, DB_PASS, DB_HOST, DB_PORT, DATABASE)
engine = create_engine(connect_string)

# The path to the output file directory
csvdir = '../output_usa'

# Get all the csv files 
csvfiles = glob.glob(os.path.join(csvdir, '*.csv'))

# Loop through the files and read them in with pandas
dataframes = []  # A list to hold all the individual pandas DataFrames
for csvfile in csvfiles:
    what_job = os.path.split(os.path.splitext(csvfile)[0])[1]
    df = pd.read_csv(csvfile)
    df = df.drop_duplicates()
    df.to_sql(name = what_job, con=engine, if_exists='append', index=False)
    engine.dispose()