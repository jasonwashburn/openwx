# OpenWx

### To Run:
Load .devcontainer in VSCode, then start development server either by using the included run/debug configuration or by running `python src/app/main.py`

Access api at http://localhost:8000/docs

Example Query:
```bash
curl -X 'GET' \
  'http://localhost:8000/queryParameters?model_run=2022-11-06T18%3A00%3A00&valid_time_start=2022-11-06T18%3A00%3A00&valid_time_end=2022-11-06T18%3A00%3A00&parameters=temperature&parameters=relative_humidity&latitude=45.0&longitude=84.0' \
  -H 'accept: application/json'
```
