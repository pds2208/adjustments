from datetime import datetime
from decimal import Decimal
from typing import Optional

import requests
from pydantic import BaseModel, ValidationError
from requests.exceptions import ConnectTimeout

from persistence.models import AdjustmentType
from sage import SageException
from util.configuration import hyper_uri, adjustments_uri, hyper_api_key, hyper_timeout
from util.logging import log


class HypersageResponse(BaseModel):
    success: bool
    code: int
    response: bool
    message: Optional[str]


def update_sage_stock(
        *,
        adj_type: int,
        quantity: Decimal,
        stock_code: str,
        reference: str,
        cost: Optional[float]
) -> Optional[str]:
    now = datetime.today()
    payload = {
        "stockCode": stock_code,
        "quantity": float(quantity),
        "type": adj_type,
        "date": now.strftime("%d/%m/%Y"),
        "reference": "Winegum Stock Adjustment",
        "details": reference.strip(),
    }

    if cost is not None:
        payload['costPrice'] = cost

    endpoint = f"{hyper_uri}{adjustments_uri}"
    log.info(f"Calling HyperSage endpoint: {endpoint}")

    try:
        r = requests.post(
            endpoint,
            headers={"AuthToken": hyper_api_key},
            timeout=hyper_timeout,
            json=payload,
            verify=False,
        )
    except ConnectTimeout:
        log.warn("Connection timeout connecting to HyperSage")
        return "Timed out connecting to HyperSage"
    except TimeoutError:
        log.warn("Connection timeout connecting to HyperSage")
        return "Timed out communicating with HyperSage"
    except Exception as e:
        log.warn(f"Error communicating with HyperSage: {e}")
        return f"Error communicating with HyperSage: {e}"

    if r.status_code != 200:
        if adj_type == AdjustmentType.adj_out:
            err = f"Cannot add an adjustment out to Sage, error status is {r.status_code}"
            log.warn(err)
            raise SageException(err + ". The product quantity on Sage may be incorrect")
        err = f"Cannot add an adjustment in to Sage, error status is {r.status_code}"
        log.warn(err)
        raise SageException(err)

    try:
        r.encoding = 'utf-8-sig'
        i = r.json()
    except Exception as e:
        log.warn(f"HyperSage did not return a valid json response: {e}")
        raise SageException(f"HyperSage did not return a valid json response: {e}")

    try:
        response = HypersageResponse(**i)
    except ValidationError as e:
        log.warn(f"Validation of Sage response failed: {e}")
        raise SageException(f"Validation of Sage response failed: {e}")

    if response.success is False:
        return f"error {response.code} from HyperSage, message: {response.message}"

    typ = "In" if adj_type == 1 else "Out"
    log.info(f"Added adjustment: Stock Code: {stock_code}, Type: {typ}, Quantity: {float(quantity)}")
    return None
