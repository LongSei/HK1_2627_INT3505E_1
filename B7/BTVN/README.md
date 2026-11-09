# BTVN Buổi 7

1. Lab 1: `app/api/products.py`
2. OrderItem, `/api/v1/orders`: `app/api/orders.py`
3. Docker: `Dockerfile`, `docker-compose.yml`
4. `/healthz`, `/ready`: `app/api/health.py`
5. pytest: `tests/test_api.py`

```bash
docker compose up --build
pytest -v
```

![](images/01_pytest.png)

![](images/02_orders.png)

![](images/03_healthz_ready.png)

![](images/04_dockerfile_compose.png)

![](images/05_docker_compose_logs.png)
