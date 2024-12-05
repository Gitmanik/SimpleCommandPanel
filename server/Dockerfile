FROM python:3.12.1-slim-bookworm

WORKDIR /python-docker
COPY . .

RUN apt update && apt install avahi-utils chromium -y
RUN pip3 install -r requirements.txt

CMD [ "flask", "--app" , "panel", "run", "--host=0.0.0.0"]
