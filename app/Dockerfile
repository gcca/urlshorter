FROM python:3.12.3-alpine3.19 AS builder

RUN apk update && apk add g++
WORKDIR /short
COPY . .
RUN env CC="g++ -std=c++20" python setup.py build_ext

FROM python:3.12.3-alpine3.19

COPY --from=builder /short/build/lib.*/short.* /usr/local/lib/python3.12/site-packages/
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade -r requirements.txt
CMD ["uvicorn", "main:app", "--reload", "--host", "0.0.0.0", "--port", "80"]
