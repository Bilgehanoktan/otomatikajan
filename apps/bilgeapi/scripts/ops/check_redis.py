import redis
import os

r = redis.Redis(host='127.0.0.1', port=6380, db=0)
queues = ['default', 'critical', 'background', 'deerflow', 'celery']

for q in queues:
    try:
        print(f"Queue [{q}] length: {r.llen(q)}")
    except Exception as e:
        print(f"Error checking {q}: {e}")

print(f"Total keys: {len(r.keys('*'))}")
r.close()
