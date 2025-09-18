# app/services.py
import requests
import json
from flask import current_app as app

# -----------------------------------------------------------------------------

def call_requests(url, headers):
    r = requests.get(url, headers=headers)
    return r

# -----------------------------------------------------------------------------

def get_s3_urls(foto_ids, token):

    headers = { 'Content-Type': 'application/json', 'x-access-token': token }
    url = app.config['AWS_S3_URL']

    #app.logger.info("S3 URL [%s]", app.config['AWS_S3_URL'])
    #app.logger.info(json.dumps({'objects': foto_ids}))

    #r = requests
    try:
        r = requests.post(url, data=json.dumps({'objects': foto_ids}), headers=headers)
    except Exception as err:
        app.logger.error(str(err))

    return r
