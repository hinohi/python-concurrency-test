# Python concurrency test

## これは何？

Python の標準的・有名な平行プログラミング用ライブラリの使い勝手や性能を検証する。

具体的には「 requests で webサーバーにリクエストを行う」というタスクを平行に実行する。

## サーバー

ベンチマーク用にパラメータを調整しやすいサーバーを用意する。

構成は nginx + uwsgi + flask。
docker でローカルに起動してテストした。

docker イメージは [tiangolo/uwsgi-nginx-flask](https://hub.docker.com/r/tiangolo/uwsgi-nginx-flask/) を利用。
設定を少しいじっている。

```sh
% cat app/uwsgi.ini
[uwsgi]
module = main
callable = app
threads = 16
% docker run -d -v $(pwd)/app:/app -p 8000:80 -e NGINX_WORKER_PROCESSES=2 -e UWSGI_CHEAPER=2 tiangolo/uwsgi-nginx-flask:python3.6
```

以下の機能をもつ

+ 単純で高速な GET
+ 任意秒数スリープ
+ 任意サイズのファイルダウンロード

## クライアント

以下を試した。

+ multiprocessing
+ threading
+ joblib
+ eventlet

プロセス・スレッドではプレフォークするワーカープールのパターンと、愚直な毎回フォークするパターンを実装した。
