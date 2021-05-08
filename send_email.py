import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from postmarker.core import PostmarkClient

import util.configuration as config


def send_email(stock_code, error: str):
    sender_email = config.sender_email
    receiver_email = config.receiver_email

    message = MIMEMultipart("alternative")
    message["Subject"] = config.subject
    message["From"] = sender_email
    message["To"] = receiver_email

    html = """
        <html>
          <body>
            <br>
            <p><b>Error threshold exceeded while adding an adjustment to Sage</b><br>
            <br>
               While updating the following product: {stock_code}, {max_errors} consecutive errors have occured<br>
               <br>
               The last error received from Sage was:<br><br>
                <i>{error}</i>
            </p>
          </body>
        </html>

    """.format(stock_code=stock_code, error=error, max_errors=config.maximum_errors)

    postmark = PostmarkClient(server_token=config.postmarker_token)

    postmark.emails.send(
        From=sender_email,
        To=receiver_email,
        Subject=config.subject,
        HtmlBody=html
    )


if __name__ == "__main__":
    send_email("LW12345", "Timeout connecting to Sage")
