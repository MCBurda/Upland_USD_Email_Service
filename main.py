
import os
import imaplib
import email
import json
import requests

host = "imap.gmail.com"
username = os.environ.get("EMAIL_USER")
password = os.environ.get("EMAIL_PASS")  # This is the Google Account App password


# Get all emails from gmail that match the formatting of Upland USD emails and are tagged as "Upland/Upland to USD"
# by custom filtering
def get_inbox(username, password):
    mail = imaplib.IMAP4_SSL(host)
    mail.login(username, password)
    mail.select("\"" + "Upland/Upland to USD" + "\"")

    _, search_data = mail.search(None, "seen") # I specify that I am only searching for "seen" emails.
    # You can change this to "Unseen" or "All".

    email_data = {}
    for num in search_data[0].split():
        print(num)
        _, data = mail.fetch(num, '(RFC822)')
        _, b = data[0]
        email_message = email.message_from_bytes(b)

        # If the email is for money paid to me, forward it to Google sheets
        if "you just got paid" in email_message["subject"]:
            for part in email_message.walk():
                if part.get_content_type() == "text/plain":
                    body = part.get_payload(decode=True).decode()
                    transaction_id = body.split("Transaction ID:")[1].split("\n")[0].strip()
                    email_data[transaction_id] = {}
                    email_data[transaction_id]["type"] = "Sell"
                    email_data[transaction_id]["date"] = body.split("Transaction Date:")[1].split("\n")[0].strip()
                    email_data[transaction_id]["property"] = body.split("Item: ")[1].split("\n")[0].strip()
                    email_data[transaction_id]["amount"] = float(body.split("Amount: USD ")[1].split("\n")[0].strip())

        # If the email is about money that I paid, change the formatting of the post data to type = Buy
        elif "You paid USD" in email_message["subject"]:
            for part in email_message.walk():
                if part.get_content_type() == "text/plain":
                    body = part.get_payload(decode=True).decode()
                    transaction_id = body.split("Transaction ID:")[1].split("\n")[0].strip()
                    email_data[transaction_id] = {}
                    email_data[transaction_id]["type"] = "Buy"
                    email_data[transaction_id]["date"] = body.split("Transaction Date:")[1].split("\n")[0].strip()
                    email_data[transaction_id]["property"] = body.split("ITEM(S)")[1].split("USD")[1].split("\n")[2].strip()
                    email_data[transaction_id]["amount"] = float(
                        body.split("TOTAL:")[1].split("\n")[0].split("USD")[1].strip())
                    print(email_data[transaction_id])

        # In any other special situation, pass
        else:
            pass

    return email_data


# I keep a local JSON file that acts as a database and stores all transaction ID of the emails in my inbox. This allows
# us to check if an email is new or old and forward only the new.
def database_check(transactions):
    # Check if database JSON file exists and if so, load all transactions in it to a variable. Else, create the
    # database and do nothing
    if os.path.isfile("./transaction_database.json"):
        with open("./transaction_database.json", "r") as file:
            database_transactions = json.loads(file.read())

    else:
        with open("./transaction_database.json", "w") as file:
            json.dump(transactions, file)
            return None

    # Iterate through each transaction found as an email and check if it already exists in the email database. If so,
    # skip it if not, put it in the database
    old_keys = database_transactions.keys()
    new_transactions = []
    for new_key in transactions.keys():
        if new_key not in old_keys:
            new_transactions.append(new_key)
            database_transactions[new_key] = transactions[new_key]
        else:
            continue

    # If no new transactions were found after comparing transaction ids, return None
    if len(new_transactions) == 0:
        return None

    # If new transactions were added to the Dict of transactions, update the Json storage file
    with open("./transaction_database.json", "w") as file:
        file.truncate()
        json.dump(database_transactions, file)

    return new_transactions


# Make a post request to the GSHEETS Endpoint
def send_to_sheets(all_transactions, new_transactions):
    post_endpoint = os.environ.get("GSHEET_ENDPOINT")

    data = {}
    for entry in new_transactions:
        if entry in all_transactions:
            data[entry] = all_transactions[entry]
    print(data)

    resp = requests.post(post_endpoint, data=json.dumps(data))
    print(resp)

    return None


if "__main__" == __name__:
    transactions = get_inbox(username, password)
    new_transactions = database_check(transactions)
    if new_transactions is None:
        print("No new transactions. No data will be sent to Google Sheets.")
        quit()
    send_to_sheets(transactions, new_transactions)
    print("Successfully executed script!")
