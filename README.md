## Indeed Weekly Jobs Scraper 

Python script to scrape job postings from Indeed (`scraper` scripts) and upload them to the MySQL database (`cleaner` scripts). Run weekly.

### Prerequisites

Install packages by pip install:
` pip install -r requirements.txt`

## Folder Structure


_SCRAPER

The input folder contains all keywords to be extracted and excluded<br>
___input<br>
    __`exclude.txt`: keywords to exclude
    __`level.txt`: title keywords to extract
    __`skills.txt`: skill keywords to extract

The job postings will be extracted as csv files into the ouput folders<br>
___output<br>
___output_usa<br>

#### Weekly  Run
These scripts will be ran initially to scrap all jobs posted in Indeed<br>
___parallel <br>
    __`scraper.py` <br>
    __`scraper_usa.py` <br>
    __`cleaner.py` <br>
    __`cleaner_usa.py` <br>
    __`args.txt`<br>: list of jobs and countries in SEA
    __`args_usa.txt`<br>: list of jobs and states in USA
    __`output`<br>


### To run
The *scraper.py* script takes in two arguments
- Job: Data Analyst, Data Engineer, Machine Learning Engineer, Data Scientist
- Country: Malaysia, Vietnam, Thailand, Singapore, Philippines, Indonesia

Example:
```
python3 scraper.py 'Data Analyst' 'Malaysia'
python3 scraper.py 'Data Scientist' 'Singapore'
```

The *scraper_usa.py* script takes in two arguments
- Job: Data Analyst, Data Engineer, Machine Learning Engineer, Data Scientist
- State: State to scrape in Abbreviation (NY, AZ, OK, etc.)

Example:
```
python3 scraper_usa.py 'Data Engineer' 'AZ'
python3 scraper_usa.py 'Machine Learning Engineer' 'NY'
```

To run the script once iterating through all the jobs and countries in the `args.txt` folder, use parallel:
```
parallel --col-sep '\t' 'python3 scraper.py {1} {2}' :::: args.txt 
parallel --col-sep '\t' 'python3 scraper_usa.py {1} {2}' :::: args_usa.txt
```

### To clean saved csv files
The *cleaner* scripts upload the extracted csv files to the database

```
python3 cleaner.py
python3 cleaner_usa.py
```

### Note
Running all the scripts concurrently might result in IP being blocked by Indeed. A shadow user agent and proxy rotation is being used in the script but they do not work very well. To circumstance this, try scraping at diffrent time and scrape for each job separately (Running the scraper script separtely at different time instead of using parallel).

Delete the old csv files every week before scraping for the new ones to prevent duplicated old job postings being uploaded to the database.

The details required to connect to the database is not included in the code here for privacy purpose. Please contact me for the database connection information.