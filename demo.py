# -*- coding: utf-8 -*-
# @Time    : 2023/7/10 10:54
# @Author  : ShaoJK
# @File    : app.py
# @Remark  :
import hashlib
import hmac
import json
import random
import time
import clickhouse_connect

from flask import Flask, render_template, request
from requests import Session

app = Flask(__name__)
client = Session()

BaseUrl = "https://cloud.datafocus.ai"
TokenUrl = "/datafocus/api/v1.0/sc/token"
SqlUrl = "/datafocus/api/v1.0/sc/sql"

TenantId = ""
SecretId = ""
SecretKey = ""

headers = {
    "Content-Type": "application/json",
    "Tenant-Id": TenantId,
    "Secret-Id": SecretId
}


@app.route("/")
def index():
    return render_template("index.html")


def sign(method, url, body, p_nonce, p_timestamp) -> str:
    plain_text = method.upper() + url + body + p_nonce + SecretId + p_timestamp
    h = hmac.new(bytes.fromhex(SecretKey), msg=plain_text.encode("utf-8"), digestmod=hashlib.sha256)
    sign_text = h.digest()
    return sign_text.hex()


def preprocess(method, url, body):
    nonce = "".join(random.sample("AaBbCcDdEeFfGgHhIiJjKkLlMmNnOoPpQqRrSsTtUuVvWwXxYyZz0123456789", 16))
    timestamp = str(int(time.time() * 1000))
    params = {
        "nonce": nonce,
        "timestamp": timestamp,
        "sign": sign(method, url, body, nonce, timestamp)
    }
    return params, body


@app.route('/token', methods=["POST"])
def token():
    params, _ = preprocess("POST", TokenUrl, "")
    response = client.post(BaseUrl + TokenUrl, params=params, headers=headers)
    return response.json()


@app.route('/sql', methods=["POST"])
def sql():
    identity = request.json.get("identity")
    params, body = preprocess("POST", SqlUrl, json.dumps({"identity": identity}))
    response = client.post(BaseUrl + SqlUrl, params=params, data=body, headers=headers)
    return response.json()


@app.route('/query', methods=["POST"])
def query():
    sql = request.json.get("sql")
    driver = clickhouse_connect.get_client(host="192.168.0.99", port=8123, database="default", username="default", password="datafocus")
    res = driver.query(sql)
    return {"result": res.result_rows}



if __name__ == '__main__':
    app.run()
