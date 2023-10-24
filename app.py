from helpers import *
import streamlit as st
import html
from streamlit_extras.add_vertical_space import add_vertical_space
import json
import subprocess
import ast


st.set_page_config(page_title="Job Scraper",layout="wide")

if ["first_start"] not in st.session_state:
    st.session_state["first_start"] = True


with open("./data/app_metadata.json", "r") as f: metadata = json.load(f) # STart script on reload 
if ((time.time() - metadata["last_scrape_time"] > (metadata["auto_scrape_frequency_in_mins"] * 60)) and (not metadata["process_busy"])) or (st.session_state["first_start"]):
    
    st.session_state["first_start"] = False
    # linux
    subprocess.Popen(["/home/shady/anaconda3/envs/py38/bin/python", "./script.py"]) # run script 
    # windows
    # subprocess.Popen(["python", "./script.py"]) # run script


with open("./data/app_metadata.json","r") as f:st.session_state["last_scrape_time"] = metadata["last_scrape_time"]
df = pd.read_csv("./data/most_recently_scraped.csv")


if "job_title" not in st.session_state:
    st.session_state["job_title"] = "Machine Learning, Deep Learning, Computer Vision"

if "location" not in st.session_state:
    st.session_state["location"] = "india"


with st.sidebar:
    st.markdown('''
    # About

    💡 <span style="color:teal">Scrape Linkedin Jobs of your choice to stay ahead of others!!!</span>
    ''', unsafe_allow_html=True)

st.title(f""":green[_{df.shape[0]} New Jobs_]""")

data_staleness = int((time.time() - st.session_state["last_scrape_time"]) / 60)
st.warning(f"This data was scraped {data_staleness} minutes ago. Click on 'Fetch Fresh Jobs' to get new jobs data",icon="⚠️")
st.markdown("---")


scrollable_css = """
<style>
.scrollable {
    max-height: 500px;
    overflow-y: auto;
}
</style>
"""
st.markdown(scrollable_css, unsafe_allow_html=True)

outer_html = """<div style="overflow:auto; width:1280px; height:850px;">"""
for index, row in df.iterrows():
        
        j_id , exp, ti_el, appli, pos, comp, loc, desc = row.values.tolist()
        link = f"https://www.linkedin.com/jobs/search?currentJobId={j_id}"
        ti_el = "UNK" if pd.isna(ti_el) else str(int(ti_el))
        appli = "UNK" if pd.isna(appli) else str(int(appli))
        exp = "UNK" if pd.isna(exp) else str(int(exp))
        comp = "UNK" if isinstance(comp, float) else comp
        loc = "UNK" if isinstance(loc, float) else loc
        desc = [] if isinstance(desc, float) else ast.literal_eval(desc) # it is a list


        link = html.escape(link)

        desc_list = []
        if desc:
            for item in desc:
                 item = item.strip()
                 if item: desc_list.append(f"<li>{item.upper() if len(item) <=3 else item}</li>")
        else: desc_list = [f"<li>NOTHING</li>"]
        

        outer_html += f"""{index+1}. <a href="{link}">{pos}</a> | {appli} applicants | {ti_el} minutes ago | {exp} years | {comp} | {loc}"""

        desc = f"""
                <details>
                    <div class="scrollable">
                        <summary>Tech Stack: <span style="color:green"><b>{len(desc)}</b></span> matches</summary>
                        <ul>
                        {''.join(desc_list)}
                        </ul>
                    </div>
                </details>
                <hr style="border-top: 1px solid black">
                """
    
        outer_html += desc


outer_html += "</div>"
st.markdown(outer_html, unsafe_allow_html=True)
