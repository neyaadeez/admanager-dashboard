FROM python:3.9-slim

WORKDIR /bbtest

RUN apt-get update && apt-get install -y \
    wget \
    unzip \
    curl \
    gnupg \
    xvfb \
    libxi6 \
    libgconf-2-4 \
    firefox-esr \
    && rm -rf /var/lib/apt/lists/*

RUN GECKODRIVER_VERSION=`curl -sS https://api.github.com/repos/mozilla/geckodriver/releases/latest | grep 'tag_name' | cut -d\" -f4` \
    && wget -O /tmp/geckodriver.tar.gz "https://github.com/mozilla/geckodriver/releases/download/${GECKODRIVER_VERSION}/geckodriver-${GECKODRIVER_VERSION}-linux64.tar.gz" \
    && tar -xzf /tmp/geckodriver.tar.gz -C /usr/local/bin/ \
    && rm /tmp/geckodriver.tar.gz

ENV FIREFOX_BIN=/usr/bin/firefox
ENV GECKODRIVER=/usr/local/bin/geckodriver

COPY ./requirements.txt /bbtest/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . /bbtest
EXPOSE 8050
CMD ["python", "app.py"]