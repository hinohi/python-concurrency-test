# -*- coding: utf-8 -*-
import time
from flask import Flask, request

app = Flask(__name__)


@app.route('/')
def hello():
    return 'Hello, world!'


@app.route('/sleep')
def sleep():
    t = float(request.args.get('time', 0))
    if t >= 0:
        time.sleep(t)
    return f'sleep {t}'


@app.route('/post', methods=['POST'])
def post():
    return request.data, 201


@app.route('/download')
def get():
    s = int(request.args.get('size', 2**20))
    return 'a' * s


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
