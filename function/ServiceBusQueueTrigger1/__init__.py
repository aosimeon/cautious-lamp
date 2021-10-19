import logging
import azure.functions as func
import psycopg2
import os
from datetime import datetime
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

def main(msg: func.ServiceBusMessage):

    notification_id = int(msg.get_body().decode('utf-8'))
    logging.info('Azure ServiceBus queue trigger processed ID: %s',notification_id)

    # TODO: Get connection to database
    host_url = os.environ["POSTGRES_URL"]
    db = os.environ["POSTGRES_DB"]
    db_user = os.environ["POSTGRES_USER"]
    passwd = os.environ["POSTGRES_PW"]

    db_connection = psycopg2.connect(
        host=host_url,
        database=db,
        user=db_user,
        password=passwd
    )
    logging.info(f"You have successfully connected to the {dbs} database")

    try:
        # TODO: Get notification message and subject from database using the notification_id
        cursor = db_connection.cursor()
        command = f"SELECT message, subject FROM notification WHERE id={str(notification_id)}"
        cursor.execute(command)
        logging.info(
            f"Notification ID {str(notification_id)}: Get message and subject")

        for row in cursor.fetchall():
            message = row[0]
            subject = row[1]

        if not message or not subject:
            error_message = f"Id {str(notification_id)}: No message or subject"
            logging.error(error_message)
            raise Exception(error_message)

        logging.info(
            f"Id {str(notification_id)}: Message '{message}', Subject '{subject}'")

        # TODO: Get attendees email and name
        command = f"SELECT first_name, last_name, email FROM attendee"
        cursor.execute(command)
        count = 0

        # TODO: Loop through each attendee and send an email with a personalized subject
        for row in cursor.fetchall():
            first_name = row[0]
            last_name = row[1]
            email = row[2]

            logging.info(
                f"Id {str(notification_id)}: First name '{first_name}', last name '{last_name}', email '{email}'")

            email_from = Email(os.environ['ADMIN_EMAIL_ADDRESS'])
            email_to = To(email)
            subject = f"Hello, {first_name}! {subject}"
            email_content = Content("text/plain", message)

            mail = Mail(email_from, email_to, subject, email_content)
            send_grid = SendGridAPIClient(os.environ['SENDGRID_API_KEY'])
            send_grid.send(mail)

            count += 1


        # TODO: Update the notification table by setting the completed date and updating the status with the total number of attendees notified
        status = f"Notified {str(count)} attendees"
        logging.info(f"Id {str(notification_id)}: {status}@{datetime.now()}")

        command = f"UPDATE notification SET status='{status}' WHERE id={str(notification_id)}"
        cursor.execute(command)

        command = f"UPDATE notification SET completed_date='{str(datetime.now())}' WHERE id={str(notification_id)}"
        cursor.execute(command)
        db_connection.commit()

    except (Exception, psycopg2.DatabaseError) as error:
        logging.error(error)
    finally:
        # TODO: Close connection
         db_connection.close()