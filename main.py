import time

import urllib3

from sage.update_sage import update_sage, pause_adjustment
from send_email import send_email
from util.configuration import maximum_errors, sleep
from util.logging import log

if __name__ == "__main__":
    num_errors = 0
    send_email_on_error = True

    urllib3.disable_warnings()

    while True:
        adj, res = update_sage()
        if res.sage_failed:
            num_errors = num_errors + 1
            if num_errors > maximum_errors and send_email_on_error:
                log.warning(
                    f"{maximum_errors} errors have occurred. Sending email alert..."
                )
                send_email(res.stock_code, res.error)
                send_email_on_error = False
                # Mark the item as paused, so we can move on to another one
                pause_adjustment(adj)
        else:
            num_errors = 0
            send_email_on_error = True

        time.sleep(sleep)
