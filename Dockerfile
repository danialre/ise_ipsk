### Build stage
FROM python:3.7-alpine as python-build
WORKDIR /app

# copy just requirements
COPY requirements.txt /app/

# install dependencies
RUN apk add --update build-base libffi-dev libressl-dev && pip install -r requirements.txt

### Run stage
FROM python:3.7-alpine
WORKDIR /app

# reinstall python packages without dev files
COPY --from=python-build /root /root
COPY requirements.txt /app/

RUN pip install -r requirements.txt && rm -rf /root/.cache && rm -rf /var/cache/apk/* && rm -rf /root/.cache

# copy everything else - this avoid rebuilding the image for small code changes
COPY *.py *.cer *.key /app/

# set up self-signed certs (if applicable)
RUN python setup_certs.py

# run app - 2443 required for Ruckus controller support
EXPOSE 2443
CMD ["python", "main.py"]
