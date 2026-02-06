FROM anasty17/mltb:latest

WORKDIR /app
RUN chmod 777 /app && mkdir -p /app/downloads && chmod 777 /app/downloads

RUN apt-get update \
	&& apt-get install -y --no-install-recommends \
		ffmpeg \
		p7zip-full \
		unrar \
	&& rm -rf /var/lib/apt/lists/*

RUN python3 -m venv mltbenv

COPY config/requirements.txt config/requirements-cli.txt ./
RUN /app/mltbenv/bin/pip install --no-cache-dir -r requirements.txt -r requirements-cli.txt

COPY . .

RUN sed -i 's/\r$//' *.sh 2>/dev/null || true

ENV PATH="/app/mltbenv/bin:$PATH"
CMD ["python3", "-m", "bot"]
