import json
import logging
from typing import List, Optional, Tuple, TypeAlias
import urllib.request

import keydb
from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import RedirectResponse
import psycopg2.extensions
import psycopg2.pool
from pydantic import BaseModel
from starlette import status

import short

app = FastAPI()


class PoolHandler:
    pool: Optional[psycopg2.pool.AbstractConnectionPool] = None


Pool: TypeAlias = psycopg2.pool.AbstractConnectionPool
Conn: TypeAlias = psycopg2.extensions.connection
Cursor: TypeAlias = psycopg2.extensions.cursor


async def get_pool():
    if PoolHandler.pool is None:
        PoolHandler.pool = psycopg2.pool.ThreadedConnectionPool(
            minconn=1,
            maxconn=20,
            user="postgres",
            password="postgres",
            host="postgres",
            port="5432",
            database="postgres",
        )
    return PoolHandler.pool


async def get_conn(pool: Pool = Depends(get_pool)):
    conn = pool.getconn()
    try:
        yield conn
        conn.commit()
    except Exception as error:
        logging.info("Error after connection: %s", error)
        conn.rollback()
        raise
    finally:
        pool.putconn(conn)


async def get_cursor(conn: Conn = Depends(get_conn)):
    cursor = conn.cursor()
    yield cursor
    cursor.close()


class KeydbPoolHandler:
    pool: Optional[keydb.ConnectionPool] = None


async def get_keydb_pool():
    if KeydbPoolHandler.pool is None:
        KeydbPoolHandler.pool = keydb.ConnectionPool(host="keydb")
    return KeydbPoolHandler.pool


KeydbPool: TypeAlias = keydb.ConnectionPool
KeyDB: TypeAlias = keydb.KeyDB


async def get_kdb(pool: KeydbPool = Depends(get_keydb_pool)):
    kdb = keydb.KeyDB(connection_pool=pool)
    yield kdb
    kdb.close()


class ShortParams(BaseModel):
    url: str


@app.post("/api/v1/short")
async def short_url(
    params: ShortParams,
    cursor: Cursor = Depends(get_cursor),
    kdb: KeyDB = Depends(get_kdb),
):
    cachedShort = kdb.get(params.url)
    if isinstance(cachedShort, str):
        return {"shortUrl": cachedShort}

    if cachedShort:
        kdb.delete(params.url)
        logging.warning("Bad cached value for url=%s: %s", params.url, cachedShort)

    cursor.execute("SELECT short FROM urls WHERE url = %s LIMIT 2", (params.url,))

    if cursor.rowcount > 1:
        logging.warning("Non unique: url=%s", params.url)

    rows: List[Tuple[str]] = cursor.fetchall()
    if rows:
        shortUrl = rows[0][0]
        kdb.set(params.url, shortUrl)
        return {"shortUrl": rows[0][0]}

    with urllib.request.urlopen("http://uidgen") as res:
        uid = json.load(res)["uid"]

    shortUrl = short.ShortUrl(uid)

    cursor.execute("INSERT INTO urls VALUES (%s, %s)", (params.url, shortUrl))
    kdb.set(params.url, shortUrl)

    return {"shortUrl": shortUrl}


@app.get("/api/v1/{shortUrl}")
async def redirect_short(
    shortUrl: str,
    cursor: Cursor = Depends(get_cursor),
    kdb: KeyDB = Depends(get_kdb),
):
    cachedUrl = kdb.get(shortUrl)
    if isinstance(cachedUrl, str):
        return RedirectResponse(
            url=cachedUrl, status_code=status.HTTP_301_MOVED_PERMANENTLY
        )

    if cachedUrl:
        kdb.delete(shortUrl)
        logging.warning("Bad cached value for short=%s: %s", shortUrl, cachedUrl)

    cursor.execute("SELECT url FROM urls WHERE short = %s LIMIT 2", (shortUrl,))

    if cursor.rowcount > 1:
        logging.warning("Non unique: short=%s", shortUrl)

    rows: List[Tuple[str]] = cursor.fetchall()
    if rows:
        url = rows[0][0]
        kdb.set(shortUrl, url)
        return RedirectResponse(url=url, status_code=status.HTTP_301_MOVED_PERMANENTLY)

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No short url")
