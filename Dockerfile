FROM ubuntu:24.04

# Install build dependencies
RUN apt-get update && apt-get install -y gcc python3 python3-venv \
python3-dev python3-pip cron tzdata

WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN python3 -mvenv /app/env
RUN /app/env/bin/pip install --upgrade pip && \ 
/app/env/bin/pip install -r requirements.txt

# Set environment variables for Python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Copy your project code
RUN mkdir /app/api_classes
COPY api_classes/mail_api.py /app/api_classes/mail_api.py
COPY main.py /app/
COPY cron_run.sh /app/
COPY entrypoint.sh /app/

# Set timezone to EST
RUN ln -fs /usr/share/zoneinfo/America/New_York /etc/localtime && dpkg-reconfigure -f noninteractive tzdata

# Add cron job
RUN echo "0 8 * * * root /app/cron_run.sh > /var/log/cron.log 2>&1" > /etc/cron.d/hexdrop

# Set permissions and apply cron job
RUN chmod 0644 /etc/cron.d/hexdrop && crontab /etc/cron.d/hexdrop

# Start cron in foreground
ENTRYPOINT ["/bin/bash", "/app/entrypoint.sh"]