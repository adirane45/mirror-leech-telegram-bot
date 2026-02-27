ARG BASE_IMAGE=python:3.11-slim

FROM ${BASE_IMAGE} AS build

WORKDIR /app
RUN python3 -m venv mltbenv

COPY requirements/ /app/requirements/
RUN /app/mltbenv/bin/pip install --no-cache-dir -r /app/requirements/prod.txt

COPY . .

RUN sed -i 's/\r$//' scripts/*.sh 2>/dev/null || true
RUN sed -i 's/\r$//' deployment/scripts/*.sh 2>/dev/null || true

FROM ${BASE_IMAGE}

WORKDIR /app
RUN chmod 777 /app && mkdir -p /app/downloads && chmod 777 /app/downloads

RUN apt-get update \
	&& apt-get install -y --no-install-recommends \
		curl \
		ca-certificates \
		openjdk-21-jre-headless \
		procps \
		ffmpeg \
		p7zip-full \
		libmagic1 \
	&& rm -rf /var/lib/apt/lists/*

# JDownloader runtime
RUN mkdir -p /JDownloader \
	&& curl -fsSL -o /JDownloader/JDownloader.jar https://installer.jdownloader.org/JDownloader.jar

COPY --from=build /app /app

ENV PATH="/app/mltbenv/bin:$PATH"
ENV PYTHONPATH="/app/src:$PYTHONPATH"
ENV PYTHONUNBUFFERED=1
WORKDIR /app
CMD ["/app/mltbenv/bin/python3", "-m", "bot"]
