FROM python:3.12.1-slim-bookworm

WORKDIR /python-docker
COPY . .

RUN apt update && apt install avahi-daemon -y
RUN apt install --no-install-recommends avahi-utils  \ 
libasound2 libatk1.0-0 libc6 libcairo2 libcups2 libdbus-1-3 \ 
libexpat1 libfontconfig1 libgcc1 libgconf-2-4 libgdk-pixbuf2.0-0 libglib2.0-0 libgtk-3-0 libnspr4 \ 
libpango-1.0-0 libpangocairo-1.0-0 libstdc++6 libx11-6 libx11-xcb1 libxcb1 \ 
libxcursor1 libxdamage1 libxext6 libxfixes3 libxi6 libxrandr2 libxrender1 libxss1 libxtst6 \ 
libnss3 libgbm1 -y
RUN pip3 install -r requirements.txt
RUN python3 download-chrome-headless-shell.py
CMD [ "flask", "--app" , "panel", "run", "--host=0.0.0.0"]
