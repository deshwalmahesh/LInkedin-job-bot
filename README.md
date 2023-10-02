# LInkedin-job-bot

NOTE:
If it doesn't run, make the `"process_busy"` as `false` and see if the difference between `"last_scrape_time"` and current time is more than `"auto_scrape_frequency_in_mins"` inside `data/app_metadata.json`

# How to use:
In the terminal do: `pip install -r requirements.txt`

Then to run the app, `streamlit run app.py` as simple as that

Reload the streamlit app everytime you hear a bugle Victory call to see the new jobs :P

# Must edit Params:
These are inside `data/app_metadata.json`
```
1. "process_busy": If process is running it's a Lock. If appp has some problem like you closed it while it was running last time,manually set it to false`. App won't run if it's `true`.
2. "last_scrape_time": Time when the latest task was run. Difference of Current `time.time()` and this value must be greater than `auto_scrape_frequency` in order to run the job automatically without interruption
3. "job_title": Job Titles seperated by comms. Here in one go, 3 different jobs wiil be searched: "Machine Learning, Deep Learning, Computer Vision"
4. "auto_scrape_frequency_in_mins": In hiw much time you want to get the jobs. If it's tool ow, it's redundant task and if it's too high, it doesn't serve the purpose of getting fresh jobs. So you can set it to 30 minutes or so
5.  "max_jobs": Maximum no of jobs you want to get for EACH title. It it's too high, it'll get all the jobs which are old and if too low, doesn't serve the purpose. You can do 25-50
6. "location": where you want to use the search for. By default it is "india"
7. "experience": Whether to include the experience filter or not. LI doesn't have a good filter so keep it false
8. "data_freshness_in_hours": How fresh of jobs you want. If it's 24, it means it'll give you all the job for the past 24 hours. Wouldn't work. So it's kept as 0.2
```

So far so good. Some issues are known some are not. Will try my best to resolve but if not please open up a merge request in case you solved it :) 
