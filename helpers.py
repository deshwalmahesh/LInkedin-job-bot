from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from selenium.common.exceptions import ElementClickInterceptedException, ElementNotInteractableException, TimeoutException
# from selenium.webdriver.chrome.options import Options
import pandas as pd
import numpy as np
from gtts import gTTS
from tqdm import tqdm
import re, time, subprocess, psutil, os
from multiprocessing import cpu_count
from pandarallel import pandarallel


pandarallel.initialize(nb_workers=cpu_count()-1)

my_words = set({" ml ","machine learning", "nlp", " cv ", " dl " "deep learning", "artificial intelligence", " ai ", "data scien", "mlop", "neural network", "natural language", "computer vision", "recommendation",
  "anomaly", "chat", "conversation", "image process", "manipulat", "analy"
 
 "regression", "classification", "cluste", "detect", "track", "segment", "generati", "diffusion", "encoder", "decoder", "supervise", "unsupervise", "shot", "enhancement", "digiti", "optical", 
 "personalis", "ocr", "nlg", "nlu"

 "mlflow","onnx", "amazon", "google","azure", "kubernet", "dvc", "sql", "mongo","flask", "fastapi","docker", "git", "aws", "gcp", "postgres", "grafana", "prometheus", "nosql",

 "python","scikit", "tensorflow", "pytorch","keras","opencv", "hugging", "spacy", "nltk" "textblob","gensim", "detectron", "paddle", "streamlit", "gradle", "matplotlib", "numpy", "pandas",
 "seaborn", "plotly", "elastic", "jupyter", "vscode", "lime", "shap",

 "transformer","rcnn", "yolo", "lstm", "convolution", "resnet", "mobilenet", "vae", "unet", "ssd", "optimizer", "large language", "bert", "rnn", "gpt", "gru", "svm", "logistic", "forest", "tree", 
 "boost", "naive", "ann", "dnn", "svm", "knn", "cnn", " t5", " tf", "filtering", "llm", "gmm", "hmm", "backprop", "gradient",
 })


def kill_all_existing_webdrivers(name = 'firefox'):
    '''
    This function kills all processes with the given name
    '''
    for proc in psutil.process_iter(['pid', 'name']):
        if proc.info['name'] == name:
            try:
                proc.kill()
            except psutil.AccessDenied:
                print(f"Access denied to kill process {proc.info['pid']}.")
            except Exception as e:
                print(f"An error occurred while trying to kill process {proc.info['pid']}: {e}")


class JobScraper:
    def __init__(self, browser = None):
        self.loc_id_map = {
        "india":"102713980","gurgaon": "115884833","gurugram":"115884833","bangalore":"105214831","bengaluru":"105214831","noida":"104869687", "pune":"114806696",
        "chennai":"114467055","hyderabad":"105556991", "calcutta":"111795395","kolkata":"111795395","delhi":"115918471","mumbai":"106164952","bombay":"106164952",
        "chandigarh":"108789272", "ahmedabad":"104990346"}

        options = Options()

        kill_all_existing_webdrivers()
        # if isinstance(browser, webdriver.edge.service.Service):
        #     self.browser= webdriver.Edge(service = browser, options=options)
        # elif isinstance(browser, str):
        #     self.browser = webdriver.Edge(browser, options=options)
        # else: self.browser = browser
        self.browser = webdriver.Firefox()
    
        self.browser.maximize_window()
      

    def _fetch_data(self,url, max_jobs:int = 50):
        data = []
        self.browser.get(url)
        try:
            WebDriverWait(self.browser, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'base-search-card__info')))
            os.system(f"""xdotool search --name 'jobs' windowminimize""") # Use xdotool to search for the window and minimize it
        except TimeoutException:
            if "We couldn’t find a match" in self.browser.page_source:
                print("No Jobs Found")
            return []

        for i in range(max_jobs//25): # With 1 scrolling, you get 25 jobs
            try:
                old_height = self.browser.execute_script("return document.body.scrollHeight")
                self.browser.execute_script(f"window.scrollTo({old_height}, document.body.scrollHeight);")
                time.sleep(2)
                if "You've viewed all jobs for this search" in self.browser.page_source: break # Early stop criteria

            except Exception as e: print(e)

        job_lists = self.browser.find_element(By.CLASS_NAME,"jobs-search__results-list").find_elements(By.TAG_NAME,"li") # All the first <ul> and it's all <li>
        for li in tqdm(job_lists):
            try:
                try:
                    li.click()
                    time.sleep(1.5)
                    gen_desc = str(li.text) # General description
                    curr_url = str(self.browser.current_url) # has job id too
                    data.append([curr_url, gen_desc, ""]) # Generl, limk, full description
                
                except (ElementClickInterceptedException,ElementNotInteractableException) as e:
                    # print("<li> element not Clickable")
                    continue
              
                try:
                    self.browser.find_element(By.CLASS_NAME, """show-more-less-button""").click() # Click on the right box to "Show More"
                    time.sleep(1)
                    data[-1][-1] = str(self.browser.find_element(By.CLASS_NAME, """show-more-less-html__markup""").text) # Full Description

                except (ElementClickInterceptedException,ElementNotInteractableException) as e: # It didn't have anything to 
                    # print("'Show more' not Clickable")
                    pass

                try:
                    applicants = str(self.browser.find_element(By.CLASS_NAME, "num-applicants__caption").text)
                    if data[-1][-1] == "": 
                        data[-1][-1] = applicants
                    else: data[-1][-1] = (applicants + " " + data[-1][-1])

                except Exception as e:
                    print(e)
                    pass

            except Exception as e: print(e)
        return data
    
    
    def fetch_job_postings(self,job_title:str, location:str = "india", posted_hrs_ago:float = 0.3, max_jobs:int = 100, experience:bool = False):
        """
        Get All the jobs data
        args:
            job_title: Name of the job you're looking for
            location: Any major location within India or "India" itself
            posted_hrs_ago: How many hours ago the job was posted. 0.5 will give you job posts max posted at half an hour ago 
            max_jobs = How many MAximum jobs to fetch
            experience: True if want to include Internship + Entry Leven Filter
        """
        # assert (posted_hrs_ago < 24), f"Yeah!! High chances you'll get a job in 30 years if you keep on serching for jobs older than {posted_hrs_ago} ago"
        self.seconds_ago = str(int(posted_hrs_ago * 3600))
        self.job_title = re.sub("\s+","%20", job_title.strip(" \n\t")).title()
        self.location = location.lower()
        self.loc_id = None
        for loc in self.loc_id_map:
            if loc in self.location:
                self.loc_id = self.loc_id_map[loc]
                break
            
        assert (self.loc_id is not None), "FFS!! Insert a proper location in India where there are chances of getting a job. That's one more reason you had to use this tool"

        exp_filter = "&f_E=2%2C1&" if experience else "" # Full time employee. 1 for internship, 2 For Entry Level, 3 for Associate etc etc
       
        url = f"https://www.linkedin.com/jobs/search?keywords={self.job_title}&location=locationId%3D&geoId={self.loc_id}&f_TPR=r{self.seconds_ago}{exp_filter}&position=1&pageNum=0"

        self.data = self._fetch_data(url, max_jobs=max_jobs)
        return self.data
        

class FormatData:
    @staticmethod
    def get_freshness(entry):
        """
        How many minutes ago this job was posted
        """
        if not isinstance(entry, str): return np.NaN
        entry = entry.lower()
        
        if "just" in entry: return 0
        if "minute" in entry: return int(entry.strip().split(" ")[0])
        if "hour" in entry: return int(entry.strip().split(" ")[0]) * 60
        if "day" in entry: return int(entry.strip().split(" ")[0]) * 60 * 24
        return np.NaN
    
    @staticmethod
    def get_applicants(entry):
        '''
        How Many applicants are there already
        '''
        if not isinstance(entry, str): return np.NaN
        entry = entry.lower()

        if "first 25" in entry: return 0
        try:
            return int(re.findall("\d+ applicants",entry)[0].replace(" applicants",""))
        except: return np.NaN
    

    @staticmethod
    def get_experience(entry):
        """
        Fetch Experience Required for the job
        """
        exp = np.NaN
        if not isinstance(entry, str): return exp
        entry = entry.lower()

        mini = 999
        for i in re.findall("\d\+|\d\s*-\s*\d|\d\s*year", entry, flags = re.IGNORECASE):
            try:
                x = int(i.replace("year","").replace("+","").strip().split("-")[0])
                if x < mini:
                    exp = x
                    mini = x
            except: continue
        return exp
    
    @staticmethod
    def get_keywords(entry):
        if not isinstance(entry, str): return []
        entry = entry.lower()
        entry = re.sub("\W", " ", entry)
        entry = re.sub("\s+", " ", entry).strip()
        found = []
        for word in my_words:
            if word in entry:
                found.append(word.title())

        return found
        

    @staticmethod
    def clean_data(data, raise_alarm = True):
        '''
        Make a DataFrame of the data
        '''
        df = pd.DataFrame(data, columns = ["Link", "info", "desc"])
        df.to_csv(f"./data/debug_recent.csv", index = None)
        
        df["Job Id"] = df["Link"].parallel_apply(lambda x: int(re.findall("JobId=\d+", x)[0].replace("JobId=", "")))
        df = df.drop_duplicates(subset=["Job Id"])

        df["info"] = df["info"].parallel_apply(lambda x: x.split("\n"))
        df["Experience Req"] = df["desc"].parallel_apply(lambda x: FormatData.get_experience(x))
        df["Time Elapsed (minutes)"] = df["info"].parallel_apply(lambda x: FormatData.get_freshness(x[-1]))
        df["Applicants"] = df["desc"].parallel_apply(lambda x: FormatData.get_applicants(x))
        df["Position"] = df["info"].parallel_apply(lambda x: x[0].strip())
        df["Company"] = df["info"].parallel_apply(lambda x: x[2])
        df["Loc"] = df["info"].parallel_apply(lambda x: x[3])

        df["Description"] = df["desc"].parallel_apply(FormatData.get_keywords)

        df = df.drop(["info", "desc", "Link"],axis = 1)
        df = df.fillna(-1) # So that you don't drop NaN Values
        df = df[(df["Applicants"] < 25) | (df["Time Elapsed (minutes)"] < 25)]
        df = df.applymap(lambda x: np.NaN if x == -1 else x) # Change back to NaN and sort

        df["Skills"] = df["Description"].parallel_apply(len)
        df = df.sort_values(by = ["Applicants", "Skills","Time Elapsed (minutes)", "Experience Req"], ascending=[1,0,1,1]).reset_index(drop = True).drop(["Skills"], axis=1)

        if raise_alarm: FormatData._raise_alert(df.shape[0])
        
        return df


    @staticmethod
    def _raise_alert(number):
        if not number: return None

        # tts = gTTS(text=f"{number} new jobs look promising", lang="en-gb")
        # tts.save("./data/tts.mp3")
        subprocess.run(["mpg123", "./data/notification.mp3"],stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        # subprocess.run(["mpg123", "./data/tts.mp3"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


class BingGPT4:
    def __init__(self, edge_webdriver = None, tone:str = "precise", wait_time:float = 45):
        '''
        Open Edge Beta to interact with Bing chat
        args:
            edge_webdriver: Either a driver object of type: selenium.webdriver.edge.webdriver.WebDriver or the path to the edge webdriver
            tone: One of ['precise', 'balanced', 'creative']
            wait_time = Wait time in seconds before sending the next query to bot. Bigger the query, slower the response. So you have to increase or decrease it
        '''
        if not isinstance(edge_webdriver, (webdriver.edge.webdriver.WebDriver, webdriver.edge.service.Service, str)): assert False, "Either provide an Selenium Edge WebDriver, or Service object or the path to webdriver"
        
        if isinstance(edge_webdriver, webdriver.edge.service.Service):
            kill_all_existing_webdrivers()
            self.driver= webdriver.Edge(service = edge_webdriver)
        elif isinstance(edge_webdriver, str):
            kill_all_existing_webdrivers()
            self.driver= webdriver.Edge(edge_webdriver)
        else: self.driver = edge_webdriver

        self.driver.maximize_window()
        self.tone = "DEFAULT" # Tone of the model. If not set as DEFAULT  then it won't load the user desired for the first time
        self._reload_bing_chat(tone) # Open Chat for first time use

        self.limit_counter = 0 # there is a limit of 5 messages and then it has to be reload again
        self.chat_history = [] # (query, response)
        self.wait_time = wait_time # Wait after sending a query to bot
        self.timer_start = time.time() #Timer to adjust the wait_time
        self.total_interactions = 0


    def _reload_bing_chat(self, tone):
        '''
        Reload bing chat and access it's chat box. There are limits to no of message as 5. so reset the limit
        args:
            tone: Tone of the model
        '''
        self.driver.get("https://www.bing.com/search?q=Bing+AI&showconv=1&FORM=hpcodx") # Get bing chat
        time.sleep(4)
        self._change_tone(tone)

        reach_chatbox_box_script = """
        return document.querySelector('cib-serp').shadowRoot
        .querySelector('cib-action-bar').shadowRoot
        .querySelector('textarea[name="searchbox"]')
        """
        self.chat_box = self.driver.execute_script(reach_chatbox_box_script)
        self.limit_counter = 0 # Reset the limit after reload


    def _change_tone(self, tone:str="precise"):
        '''
        Change the tone of the current model. Only works if existing tone is different from given
        '''
        tone = tone.lower()

        if tone != self.tone:
            print(f"Changing Tone from {self.tone} to {tone}")
            self.tone = tone
            self.query_length_limit = 3999 if self.tone not in "balanced" else 1999 # Limits provided by Bing model

            model_tone_selector = f"""
            return document.querySelector('cib-serp').shadowRoot
            .querySelector('cib-conversation').shadowRoot
            .querySelector('cib-welcome-container').shadowRoot
            .querySelector('cib-tone-selector').shadowRoot
            .querySelector('button.tone-{self.tone}')
            """
            self.driver.execute_script(model_tone_selector).click()
            time.sleep(1.5)


    def _get_response(self):
        '''
        Get recent Response from the model. 
        '''
        sleep_time = (self.wait_time - (time.time() - self.timer_start))
        time.sleep(max(0, sleep_time))

        # Have escaped one { with another {
        bot_response_script = f"""
        var turns = document.querySelector('cib-serp').shadowRoot
        .querySelector('cib-conversation').shadowRoot
        .querySelectorAll('cib-chat-turn')[{self.limit_counter - 1}].shadowRoot
        .querySelectorAll('cib-message-group')[1].shadowRoot
        .querySelectorAll('cib-message');
        
        var texts = [];
        for (var i = 0; i < turns.length; i++) {{{{
            var shared = turns[i].shadowRoot.querySelector('cib-shared');
            if (shared) {{{{
                texts.push(shared.innerText);
            }}}}
        }}}}
        return texts;"""
        try:
            response = "\n".join(self.driver.execute_script(bot_response_script)).strip()
            return response
        
        except: return "Unable to get response. Try increasing the wait 'delay' or Force Reload Bing"
    

    def _send_data(self,text, stream = False):
        """
        Send the data to the client. We use SHIFT+ENTER because "\n" is considered as a new line by the client
            args:
                element: Element where we want to send the data
                text: Text string
                stream: Whether to send one character at a time or in bulk. If send in bulk, "\n" is converted to " " and a chunk of 1000 words is sent
        """
        if stream:
            for character in text:
                if character == "\n":
                    self.chat_box.send_keys(Keys.SHIFT + Keys.ENTER) # Send SHIFT + ENTER
                else:
                    self.chat_box.send_keys(character) # Send the character
        
        else:
            text = text.replace("\n", " ")
            for i in range(0, len(text), 1000): # More than 1200 length is not acceptable by the model at once
                chunk = text[i:i+1000]
                self.chat_box.send_keys(chunk)
        
        self.chat_box.send_keys(Keys.ENTER)


    def chat(self, query:str, tone:str = "precise", stream = False):
        '''
        Chat with the Bing Agent. It supports only 1250 Characters. Rest of it will be trimmed
        args:
            query: Your Query moxed with prompt
            tone: Tone of the model. One of ['precise', 'balanced', 'creative']
            stream: Whether to send the whole data at once or human like one character at a time
        '''
        query = query.strip()
        self._change_tone(tone)
        
        if self.limit_counter >= 5:
            self._reload_bing_chat(self.tone) # Reload the Chat again. Previous messages will be deleted and limit_cunter will be set to 0

        if self.total_interactions > 0:
            sleep_time = (self.wait_time - (time.time() - self.timer_start)) # How many seconds have it been since last interaction
            time.sleep(max(0, sleep_time))  # Wait accordingly # If timer is remaining, then wait for some time else proceed

        self.chat_box.clear()
        time.sleep(0.2)
        try:
            self._send_data(query[:self.query_length_limit], stream)
        except: return "Message sending failed. Try Force Reload Bing or increse the 'delay' to see if it help"

        time.sleep(0.5)
        self.timer_start = time.time()
        self.limit_counter += 1 # We only get 5 interactions

        response = self._get_response()
        self.chat_history.append([query,response])
        self.total_interactions += 1
        return response