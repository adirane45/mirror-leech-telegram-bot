FROM anasty17/mltb:latest

WORKDIR /app
RUN chmod 777 /app

RUN apt-get update \
	&& apt-get install -y --no-install-recommends \
		ffmpeg \
		p7zip-full \
		unrar \
	&& rm -rf /var/lib/apt/lists/*

RUN python3 -m venv mltbenv

COPY requirements.txt .
RUN mltbenv/bin/pip install --no-cache-dir -r requirements.txt

COPY . .

RUN sed -i 's/\r$//' *.sh

CMD ["bash", "start.sh"]
