FROM opengrid/dev:python3

# install all dependencies for OpenGrid website
ADD requirements.txt /usr/local/website/requirements.txt
RUN pip install -r /usr/local/website/requirements.txt

# create volume for the source code of the website
VOLUME /usr/local/website

WORKDIR /usr/local/website
CMD python3 website.py