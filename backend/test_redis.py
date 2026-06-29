import redis

try:
    client = redis.Redis(host='localhost', port=6379, decode_responses=True)
    client.ping()
    print("Redis Connection: SUCCESS")
except Exception as e:
    print("Redis Connection: FAILED")
    print("Error:", e)
