import urllib.parse
from typing import Union, Optional

import requests
from requests.exceptions import ConnectTimeout

from sage import SageException
from util.configuration import (
    sage_host,
    sage_port,
    sage_stock_uri,
    sage_user,
    sage_password,
    sage_timeout, )
from util.logging import log


def _call_sage(endpoint: str, payload: dict) -> Optional[float]:
    log.debug("Calling sage")
    try:
        r = requests.get(
            endpoint,
            auth=(sage_user, sage_password),
            params=payload,
            timeout=sage_timeout,
        )
    except ConnectTimeout:
        log.error("Connection timeout connecting to Sage")
        raise SageException("Timed out connecting to Sage")
    except TimeoutError:
        log.error("Connection timeout connecting to Sage")
        raise SageException("Timed out communicating with Sage")
    except Exception as e:
        log.error(f"Error communicating with Sage: {e}")
        raise SageException(f"Error communicating with Sage: {e}")

    log.debug(f"Sage returned a status of {r.status_code}")
    if r.status_code != 200:
        log.error(f"Sage returned an error status of: ({r.status_code}) {r.reason}")
        raise SageException(f"Sage returned an error status of: ({r.status_code}) {r.reason}")

    j = r.json()

    if len(j["$resources"]) == 0:
        return None
    return j["$resources"][0]["cost"]


def get_sage_stock(stock_code: str) -> Optional[float]:
    payload = {"select": "cost", "format": "json", "where": f"reference eq '{stock_code}'"}
    pl: str = urllib.parse.quote(payload["where"])
    payload["where"] = pl
    endpoint = f"http://{sage_host}:{sage_port}{sage_stock_uri}"

    return _call_sage(endpoint, payload)


def get_sage_cost_price(stock_code: str) -> Optional[float]:
    try:
        res = get_sage_stock(stock_code)
    except Exception as err:
        log.error(f"Exception retrieving Sage stock {err}")
        raise err

    return res


if __name__ == "__main__":
    product = "BLOTCH05"
    print(f"Cost price for {product} is: {get_sage_cost_price(product)}" )
