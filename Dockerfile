FROM python:3.9.1-slim-buster

COPY . /lw
WORKDIR /lw

ENV DATABASE_URL=${DATABASE_URL}
ENV PYTHONPATH "${PYTHONPATH}:/lw/lewisandwood"

ENV OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES
ENV RUNTIME=None

RUN pip --trusted-host pypi.python.org --trusted-host pypi.org --trusted-host files.pythonhosted.org install -r requirements.txt

CMD [ "python", "./update_sage.py" ]
