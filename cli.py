# -*- coding: utf-8 -*-
import argparse
import sys
import time
import requests


HOST = 'http://localhost:8000'


def _serializable_func(args):
    id_, a, k = args
    res = requests.request(*a, **k)
    return [id_, res.text]


def cli_series(num, conc, args, kwargs):
    for i in range(num):
        print([i, requests.request(*args, **kwargs).text])


def cli_process_honest(num, conc, args, kwargs):
    from multiprocessing import Process, Pipe

    def f(id_, c, *a, **k):
        res = requests.request(*a, **k)
        c.send([id_, res.text])

    for i in range(num // conc):
        job_list = []
        for j in range(conc):
            parent_conn, child_conn = Pipe()
            job = Process(target=f, args=(i * conc + j, child_conn, *args), kwargs=kwargs)
            job.start()
            job_list.append([job, parent_conn])
        for job, parent_conn in job_list:
            job.join()
            print(parent_conn.recv())


def cli_thread_honest(num, conc, args, kwargs):
    from queue import Queue
    from threading import Thread

    def f(id_, q, *a, **k):
        res = requests.request(*a, **k)
        q.put([id_, res.text])

    for i in range(num // conc):
        job_list = []
        q = Queue()
        for j in range(conc):
            id_ = i * conc + j
            job = Thread(target=f, args=(id_, q, *args), kwargs=kwargs)
            job.start()
            job_list.append(job)
        for job in job_list:
            job.join()
        while not q.empty():
            print(q.get())


def cli_process_pool(num, conc, args, kwargs):
    from multiprocessing import Pool

    with Pool(conc) as p:
        it = ((i, args, kwargs) for i in range(num))
        for result in p.imap(_serializable_func, it):
            print(result)


def cli_thread_pool(num, conc, args, kwargs):
    from queue import Queue
    from threading import Thread

    def worker(iq, oq):
        while True:
            item = iq.get()
            if item is None:
                return
            id_, a, k = item
            res = requests.request(*a, **k)
            oq.put([id_, res.text])

    def printer(n, oq):
        for _ in range(n):
            print(oq.get())

    iq = Queue()
    oq = Queue()
    workers = []
    for _ in range(conc):
        w = Thread(target=worker, args=(iq, oq))
        w.start()
        workers.append(w)

    p = Thread(target=printer, args=(num, oq))
    p.start()

    for i in range(num):
        iq.put((i, args, kwargs))

    p.join()
    for _ in range(conc):
        iq.put(None)
    for w in workers:
        w.join()


def cli_joblib_process(num, conc, args, kwargs):
    from joblib import Parallel, delayed

    tasks = (delayed(_serializable_func)((i, args, kwargs)) for i in range(num))
    for result in Parallel(n_jobs=conc)(tasks):
        print(result)


def cli_joblib_thread(num, conc, args, kwargs):
    from joblib import Parallel, delayed

    tasks = (delayed(_serializable_func)((i, args, kwargs)) for i in range(num))
    for result in Parallel(n_jobs=conc, backend='threading')(tasks):
        print(result)


def cli_eventlet_pool(num, conc, args, kwargs):
    import eventlet

    def f(item):
        id_, a, k = item
        res = requests.request(*a, **k)
        return [id_, res.text]

    pool = eventlet.GreenPool(conc)
    for result in pool.imap(f, ((i, args, kwargs) for i in range(num))):
        print(result)


def main():
    test_types = {
        'hello': [
            ('GET', HOST),
            {},
        ],
        'post': [
            ('POST', HOST+'/post'),
            {'data': 'a' * 2**20},
        ],
        'sleep': [
            ('GET', HOST+'/sleep'),
            {'params': {'time': 1}},
        ],
        'download': [
            ('GET', HOST+'/download'),
            {'params': {'size': 2**20}},
        ],
    }
    func_types = {
        'series': cli_series,
        'process_honest': cli_process_honest,
        'thread_honest': cli_thread_honest,
        'process_pool': cli_process_pool,
        'thread_pool': cli_thread_pool,
        'joblib_process': cli_joblib_process,
        'joblib_thread': cli_joblib_thread,
        'eventlet_pool': cli_eventlet_pool,
    }
    parser = argparse.ArgumentParser('concurrency test')
    parser.add_argument('--num', '-n',
                        type=int, default=100)
    parser.add_argument('--concurrency', '-c',
                        type=int, default=1)
    parser.add_argument('--type', '-t',
                        choices=list(test_types),
                        default='index')
    parser.add_argument('func', choices=list(func_types))
    args = parser.parse_args()

    print(f'func={args.func} times={args.num} concurrency={args.concurrency} type={args.type}', file=sys.stderr)

    a, k = test_types[args.type]
    func = func_types[args.func]

    start = time.time()
    func(args.num, args.concurrency, a, k)
    end = time.time()

    print(f'time={end - start:.5}', file=sys.stderr)


if __name__ == '__main__':
    main()
