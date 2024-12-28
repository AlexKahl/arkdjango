FROM python:3.9

LABEL maintainer="Alex Kahl"

ENV PYTHONUNBUFFERED 1


COPY ./requirements.txt /requirements.txt
COPY ./app /app
COPY ./.ssh /.ssh
COPY ./scripts /scripts

WORKDIR /app
EXPOSE 8000


#RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y python-setuptools

ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

RUN pip install --upgrade setuptools && pip install -r /requirements.txt

# FIXME: cloning the repo directly from git using ssh
COPY ./build /build
#RUN pip install /build/bbccode/.

# FIXME: cloning repo directly from git
#RUN \
#  chmod 600 /.ssh && \
#  apt-get install --yes --no-install-recommends \
#    openssh-client \
#    && apt-get clean && \
#  ssh-keyscan -H github.com github.org >> /.ssh/known_hosts && \
#  #ssh-keyscan github.org >> /.ssh/known_hosts && \
#  #cho "IdentityFile /repo-key" >> /etc/ssh/ssh_config && \
#  #echo -e "StrictHostKeyChecking no" >> /etc/ssh/ssh_config && \
#  git clone git@github.com:bluebalancecapital/bbccode.git


RUN adduser --disabled-password --no-create-home app && \
    mkdir -p /vol/web/static && \
    mkdir -p /vol/web/media && \
    chown -R app:app /vol && \
    chmod -R 755 /vol && \
    chmod -R +x /scripts

ENV PATH="/scripts:/py/bin:$PATH"

USER app

CMD ["run.sh"]

