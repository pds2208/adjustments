import urllib.parse
from typing import Optional

import requests
from pydantic import BaseModel, Field, ValidationError
from requests.exceptions import ConnectTimeout

from sage import SageException
from util.configuration import (
    sage_stock_uri,
    sage_user,
    sage_password,
    sage_timeout, )
from util.logging import log


class Resource(BaseModel):
    url: str = Field(..., alias='$url')
    uuid: str = Field(..., alias='$uuid')
    httpStatus: str = Field(..., alias='$httpStatus')
    descriptor: str = Field(..., alias='$descriptor')
    cost: float


class SageResponse(BaseModel):
    descriptor: str = Field(..., alias='$descriptor')
    url: str = Field(..., alias='$url')
    totalResults: int = Field(..., alias='$totalResults')
    startIndex: int = Field(..., alias='$startIndex')
    itemsPerPage: int = Field(..., alias='$itemsPerPage')
    resources: list[Resource] = Field(..., alias='$resources')


def _call_sage(endpoint: str, payload: dict) -> Optional[float]:
    log.debug("Calling sage")
    try:
        r = requests.get(
            endpoint,
            auth=(sage_user, sage_password),
            params=payload,
            timeout=sage_timeout,
            verify=False,
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

    try:
        r.encoding = 'utf-8-sig'
        j = r.json()
    except Exception as e:
        log.error(f"Sage did not return a valid json response: {e}")
        raise SageException(f"Sage did not return a valid json response: {e}")

    try:
        sage_response = SageResponse(**j)
    except ValidationError as e:
        log.error(f"Validation of Sage response failed: {e}")
        raise SageException(f"Validation of Sage response failed: {e}")

    if len(sage_response.resources) == 0:
        return None
    return sage_response.resources[0].cost


def get_sage_cost_price(stock_code: str) -> Optional[float]:
    try:
        payload = {"select": "cost", "format": "json", "where": f"reference eq '{stock_code}'"}
        payload["where"] = urllib.parse.quote(payload["where"])
        res = _call_sage(sage_stock_uri, payload)
    except Exception as err:
        log.error(f"Exception retrieving Sage stock ", exc_info=1)
        raise err

    return res


if __name__ == "__main__":
    product = "BLOTCH05"
    print(f"Cost price for {product} is: {get_sage_cost_price(product)}")
