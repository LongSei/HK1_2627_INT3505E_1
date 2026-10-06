# Bài 1 · Endpoint đầu tiên trả JSON

`GET /` trả `{"message": "Hello, API!"}` với `Content-Type: application/json`.

```bash
python3 app.py
curl -i http://127.0.0.1:5001/
```

![curl](images/01_hello.png)

![server](images/server_log.png)
