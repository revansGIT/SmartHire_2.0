import imaplib

mail = imaplib.IMAP4_SSL("imap.gmail.com")
mail.login("watcherk001@gmail.com", "pwha ofhh txie akee")
mail.select("INBOX")
status, messages = mail.search(None, "ALL")
print("Status:", status)
print("Emails found:", len(messages[0].split()))
