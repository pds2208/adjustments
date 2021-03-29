import urllib.parse

import requests
from requests.exceptions import ConnectTimeout

from util.configuration import (
    sage_host,
    sage_port,
    sage_stock_uri,
    sage_user,
    sage_password,
    sage_timeout, )
from util.logging import log


def _call_sage(endpoint, payload):
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
        raise Exception("Timed out connecting to Sage")
    except TimeoutError:
        log.error("Connection timeout connecting to Sage")
        raise TimeoutError("Timed out communicating with Sage")
    except Exception as e:
        log.error(f"Error communicating with Sage: {e}")
        raise Exception(f"Error communicating with Sage: {e}")

    log.debug(f"Sage returned a status of {r.status_code}")
    if r.status_code != 200:
        log.error(f"Sage returned an error status of: ({r.status_code}) {r.reason}")
        raise Exception(f"Sage returned an error status of: ({r.status_code}) {r.reason}")

    j = r.json()
    return j["$resources"][0]["cost"]


def get_sage_stock(stock_code: str) -> float:
    payload = {"select": "cost", "format": "json", "where": f"reference eq '{stock_code}'"}
    pl: str = urllib.parse.quote(payload["where"])
    payload["where"] = pl
    endpoint = f"http://{sage_host}:{sage_port}{sage_stock_uri}"

    return _call_sage(endpoint, payload)


def get_cost_price(product: str) -> float:
    try:
        res = get_sage_stock(product)
    except Exception as err:
        log.error(f"Exception retrieving Sage stock {err}")
        raise err
    if res is None:
        return 0.0

    return res


if __name__ == "__main__":
    print(get_sage_stock("BLOTCH05"))
