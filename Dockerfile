FROM python:3.8

# install google chrome
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add -
RUN sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list'
RUN apt-get -y update
RUN apt-get install -y google-chrome-stable

# install chromedriver
RUN apt-get install -yqq unzip
RUN wget -O /tmp/chromedriver.zip http://chromedriver.storage.googleapis.com/`curl -sS chromedriver.storage.googleapis.com/LATEST_RELEASE`/chromedriver_linux64.zip
RUN unzip /tmp/chromedriver.zip chromedriver -d /usr/local/bin/

RUN apt-get install -yqq mpg123

RUN mkdir -p /root/.streamlit

RUN bash -c 'echo -e "\
[general]\n\
email = \"your-email@domain.com\"\n\
" > /root/.streamlit/credentials.toml'

# set display port to avoid crash
ENV DISPLAY=:99

# upgrade pip
RUN pip install --upgrade pip

# Set the working directory in the container to /app
WORKDIR /app

COPY ./requirements.txt /app/requirements.txt

RUN pip install --upgrade -r /app/requirements.txt

# Add the current directory contents into the container at /app
ADD . /app


# Run script.py when the container launches
CMD ["streamlit", "run", "main.py", "--server.port", "9999"]
