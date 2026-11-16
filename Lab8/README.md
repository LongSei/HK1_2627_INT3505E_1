# Buổi 8

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r "Lab 1/requirements.txt"
```

## Lab 1

`Lab 1/tests/test_lab01.py` (4 test + bonus `test_response_extra_field_blocked`)

```bash
cd "Lab 1"
python -m pytest -v
```

![](Lab%201/images/pytest.png)

## Lab 2

`Lab 2/openapi.yaml`, `Lab 2/.spectral.yml`, `Lab 2/spectral.log`

Custom rule `response-200-schema-not-empty`: bắt response 200 có schema rỗng (không có field nào).

```bash
cd "Lab 2"
npx -y @stoplight/spectral-cli@6 lint openapi.yaml --ruleset .spectral.yml
```

![](Lab%202/images/spectral.png)

## Lab 3

`Lab 3/books-api.postman_collection.json` (folder `error-cases`), `Lab 3/newman.sh`, `Lab 3/reports/junit.xml`

```bash
cd "Lab 3"
python -m app --port 5000
./newman.sh
```

![](Lab%203/images/newman.png)

## Lab 4

`Lab 4/performance/locustfile.py` (`search_by_year`), `Lab 4/reports/A.html`, `B.html`, `C.html`, `Lab 4/performance/analysis.md`

```bash
cd "Lab 4"
python -m app --port 5000
locust -f performance/locustfile.py --headless -H http://127.0.0.1:5000 -u 10 -r 2 -t 30s --html reports/A.html
locust -f performance/locustfile.py --headless -H http://127.0.0.1:5000 -u 50 -r 5 -t 60s --html reports/B.html
locust -f performance/locustfile.py --headless -H http://127.0.0.1:5000 -u 200 -r 50 -t 30s --html reports/C.html
```

## BTVN

`BTVN/locustfile.py`, `BTVN/reports/u50.html` … `u800.html`, `BTVN/analysis.md`

```bash
cd BTVN
for u in 50 200 400 800; do locust -f locustfile.py --headless -H http://127.0.0.1:5000 -u $u -r 50 -t 40s --html reports/u$u.html; done
```
