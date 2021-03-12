FROM python:3.9.1-slim-buster

COPY . /lw
WORKDIR /lw

RUN chmod +x start.sh

ENV DATABASE_URL=${DATABASE_URL}
ENV PYTHONPATH "${PYTHONPATH}:/lw/lewisandwood"

RUN apt-get update && \
    apt-get install -y locales apt-transport-https ca-certificates curl software-properties-common gcc && \
    sed -i -e 's/# en_GB.UTF-8 UTF-8/en_GB.UTF-8 UTF-8/' /etc/locale.gen && \
    dpkg-reconfigure --frontend=noninteractive locales

ENV LC_ALL=en_GB.UTF-8
ENV FLASK_ENV=production
ENV RUNTIME=docker
ENV OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES

RUN pip --trusted-host pypi.python.org --trusted-host pypi.org --trusted-host files.pythonhosted.org install -r requirements.txt

CMD [ "python", "./update_sage.py" ]
