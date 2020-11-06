## Indeed Weekly Jobs Scraper 

### Prerequisites

Install packages by pip install:
` pip install -r requirements.txt`

## Folder Structure


_SCRAPER

The input folder contains all keywords to be extracted and excluded<br>
___input<br>

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
    __`args.txt`<br>
    __`args_usa.txt`<br>
    __`output`<br>


### To run
```
parallel --col-sep '\t' 'python3 scraper.py {1} {2}' :::: args.txt 
parallel --col-sep '\t' 'python3 scraper_usa.py {1} {2}' :::: args_usa.txt
```

### To clean saved csv files

```
python3 cleaner.py
python3 cleaner_usa.py
```

### Note
Running all the scripts concurrently might result in IP being blocked by Indeed. A shadow user agent and proxy rotation is being used in the script but they do not work very well. To circumstance this, try scraping at diffrent time and scrape for each job separately (Running the scraper script separtely at different time instead of using parallel).

Please contact me for the database connection information.
