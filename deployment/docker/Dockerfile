ARG BASE_IMAGE=anasty17/mltb@sha256:cc58f595bb12bab00c373069a4a90169ab4fe470ee5084c87690dc92899fcfd6

FROM ${BASE_IMAGE} AS build

WORKDIR /app
RUN python3 -m venv mltbenv

COPY requirements/prod.txt /tmp/requirements.txt
RUN /app/mltbenv/bin/pip install --no-cache-dir -r /tmp/requirements.txt

COPY . .

RUN sed -i 's/\r$//' scripts/*.sh 2>/dev/null || true
RUN sed -i 's/\r$//' deployment/scripts/*.sh 2>/dev/null || true

FROM ${BASE_IMAGE}

WORKDIR /app
RUN chmod 777 /app && mkdir -p /app/downloads && chmod 777 /app/downloads

RUN apt-get update \
	&& apt-get install -y --no-install-recommends \
		ffmpeg \
		p7zip-full \
		unrar \
	&& rm -rf /var/lib/apt/lists/*

COPY --from=build /app /app

ENV PATH="/app/mltbenv/bin:$PATH"
ENV PYTHONPATH="/app/src:$PYTHONPATH"
ENV PYTHONUNBUFFERED=1
WORKDIR /app
CMD ["/app/mltbenv/bin/python3", "-m", "bot"]
