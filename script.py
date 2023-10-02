from helpers import *
import json


def scrape():
    data = []
    with open("./data/app_metadata.json", "r") as f: metadata = json.load(f) # Open file 
    metadata["process_busy"] = True

    try:
        print("Starting Scraping.....")

        with open("./data/app_metadata.json", "w") as f: json.dump(metadata, f) # acquire lock 

        for job_title in metadata["job_title"].split(","):
            JS = JobScraper()
            sub_data = JS.fetch_job_postings(job_title, posted_hrs_ago = (metadata["data_freshness_in_hours"]), max_jobs = metadata["max_jobs"])
            data.extend(sub_data)

            try: # Extra computation but worth it because while it is being scraped, we can apply
                df = FormatData.clean_data(data, raise_alarm = False)
                df.to_csv("./data/most_recently_scraped.csv", index = None) # So that streamlit can open it
            except Exception as e:
                print(e)
                pass
        
        JS.browser.quit()

        df = FormatData.clean_data(data,)
        metadata["last_scrape_time"] = time.time()

        if df.shape[0]:
            df.to_csv(f"./data/AI_{str(time.time())}.csv", index = None)
            df.to_csv("./data/most_recently_scraped.csv", index = None) # So that streamlit can open it
        
        metadata["last_scrape_time"] = time.time()
        metadata["process_busy"] = False # release lock
        with open("./data/app_metadata.json", "w") as f: json.dump(metadata, f) # Update file

    except Exception as e: 
        print(e)
        metadata["process_busy"] = False # release lock
        with open("./data/app_metadata.json", "w") as f: json.dump(metadata, f) 


while True:
    print("Launched Script..")
    with open("./data/app_metadata.json", "r") as f: metadata = json.load(f) # Open file 
    if (time.time() - metadata["last_scrape_time"] > (metadata["auto_scrape_frequency_in_mins"] * 60)) and (not metadata["process_busy"]):
        scrape()
    else: time.sleep(60)