FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

WORKDIR /python-docker
COPY . .

RUN apt update && apt install avahi-daemon -y
RUN uv sync
CMD [ "uv", "run", "flask", "--app" , "panel", "run", "--host=0.0.0.0"]
