#!/usr/bin/env python

# Adapted from:
# http://wboptimum.com/splitting-gmail-mbox-by-label/

import sys
import getopt
import mailbox
from email.header import decode_header, make_header

def main(argv):
	in_mbox = "source.mbox"
	prefix = ""
	try:
		opts, args = getopt.getopt(argv, "i:p:", ["infile=", "prefix="])
	except getopt.GetoptError:
		print("python splitgmail.py -i <infile> -p <prefix>")
		sys.exit(2)

	for opt, arg in opts:
		if opt in ("-i", "--infile"):
			in_mbox = arg
		elif opt in ("-p", "--prefix"):
			prefix = arg

	print("Processing file \"" + in_mbox + "\", output prefix \"" + prefix + "\"")
	sys.stdout.flush()

	# Create common mailboxes
	boxes = {
		"Inbox":	mailbox.mbox(prefix + "INBOX", create=True),
		"Sent":		mailbox.mbox(prefix + "Sent", create=True),
		"Archive":	mailbox.mbox(prefix + "Archive", create=True),
		"Spam":	mailbox.mbox(prefix + "Spam", create=True),
		"Chat":	mailbox.mbox(prefix + "Chat", create=True),
		"Trash":	mailbox.mbox(prefix + "Trash", create=True),
	}

	sourcembox = mailbox.mbox(in_mbox, create=False)
	sys.stdout.flush()

	mcount = mjunk = mchat = msaved = merr_hdr = merr_cont = 0

	def decode(s):
		# https://stackoverflow.com/questions/7331351/python-email-header-decoding-utf-8
		# https://www.base64decode.org/
		try:
			result = str(make_header(decode_header(s)))
		except:
			# print("Error decoding header: " + s)
			dh=decode_header(s)
			# print("Decode: " + str(dh))
			l=[]
			for hdr,enc in dh:
				if (enc == 'iso-8859-8-i'):
					enc='iso-8859-8'
				l.append((hdr,enc))
			h=make_header(l)
			# print("Make header:" + str(h))
		return result

	print("Looping:")
	labels={}
	for message in sourcembox:
		read = True
		flagged = False
		mcount += 1
		gmail_labels = message["X-Gmail-Labels"]
		tbox = "Archive"				# default target box: Archive

		if gmail_labels:
			gmail_labels = decode(gmail_labels)
			gmail_labels = gmail_labels.split(',')	# from here we only work on an array to avoid partial matches
			# handle flags
			if "Unread" in gmail_labels:
				read = False
			if "לא נקרא" in gmail_labels:
				read = False
			if "נפתח" in gmail_labels:
				read = True
			if "Starred" in gmail_labels:
				flagged = True

			# order matters!
			if "Spam" in gmail_labels:
				mjunk += 1
				tbox = "Spam"
			elif "Chat" in gmail_labels:
				mchat += 1
				tbox = "Chat"
			elif "Trash" in gmail_labels:
				tbox = "Trash"
			elif "אשפה" in gmail_labels:
				tbox = "Trash"
			elif "Sent" in gmail_labels:		# anything that has Sent goes to Sent box
				tbox = "Sent"
			elif "דואר יוצא" in gmail_labels:	# anything that has Sent goes to Sent box
				tbox = "Sent"
			elif "Inbox" in gmail_labels:		# Inbox treated here because some messages can be Sent,Inbox
				tbox = "Inbox"
			elif "תיבת דואר נכנס" in gmail_labels:		# Inbox treated here because some messages can be Sent,Inbox
				tbox = "Inbox"
			elif "קטגוריה – אישי" in gmail_labels:		# Inbox treated here because some messages can be Sent,Inbox
				tbox = "Inbox"
			else:
				for label_ in gmail_labels:
					label=label_.replace('/','__') # Handle sublabels in gmail
					# ignore meta labels
					if label in ["Important","Unread","Starred","Newsletters"]:
						continue
					if label in ["חשוב","לא נקרא","נפתח","קטגוריה – עדכונים", "קטגוריה – קידומי מכירות","קטגוריה – רשתות חברתיות"]:
						continue

					# use last match (no break on loop)
					tbox = label
					if label not in labels:
						labels[label] = 1
					else:
						labels[label] += 1

					# handle odd labels
					if label == "[Imap]/Archive":
						tbox = "Archive"
					elif label == "מאוחסן בארכיון":
						tbox = "Archive"
				
				# if nothing matched we'll use default set at message loop start

		# fixup missing status flags in the message
		if read:
			message["Status"] = "RO"
		else:
			message["Status"] = "O"
		if flagged:
			message["X-Status"] = "F"

		try:
			mfrom = decode(message["From"]) or "Unknown"
		except:
			# print("Error decoding From: " + message["From"])
			merr_hdr += 1
			mfrom = "Unknown"
		mid = message["Message-Id"] or "<N/A>"
		# print("Storing " + mid + " from \"" + mfrom + "\" to mbox \"" + tbox + "\"")
		msaved += 1

		if tbox not in boxes:
			boxes[tbox] = mailbox.mbox(prefix + tbox, create=True)
		# https://stackoverflow.com/questions/409217/python-mailbox-encoding-errors
		try:
			boxes[tbox].add(message)
		except UnicodeEncodeError:
			# print("Error adding message to mbox: " + tbox)
			# print(f"Message: {message}")
			# print("From: " + mfrom)
			# print("Message ID: " + mid)
			merr_cont += 1

			email_messages = get_email_list(message)
			for i, msg in enumerate(email_messages):
				content_type = 'NA' if isinstance(msg, str) else msg.get_content_type()
				encoding = 'NA' if isinstance(msg, str) else msg.get('Content-Transfer-Encoding', 'NA')
				# print(f'{i} - {content_type} - {encoding}')
				if 'text/plain' in content_type and 'base64' not in encoding:
					try:
						hdr=decode_header(msg['Subject'])
						enc=hdr[0][1]
						msg.set_charset(enc)
					except:
						# print('Error transfering header')
						pass
				elif 'multipart/alternative' in content_type and 'base64' not in encoding:
					try:
						hdr=decode_header(msg['Subject'])
						enc=hdr[0][1]
						msg.set_charset(enc)
					except:
						# print('Error transfering header')
						pass
				try:
					boxes[tbox].add(msg)
				except:
					pass
					# print('Error adding message')
					# print(f"Message: {msg}")

	print(str(mcount) + " messages processed, " + str(msaved) + " messages saved")
	print("ignored: " + str(merr_hdr) + " hdr encoding errors, " + str(merr_cont) + " content encoding error")
	print("File originally contained " + str(sourcembox.__len__()) + " messages to process")
	print("Found " + str(len(labels)) + " unique labels")
	print_dict(labels)

def get_email_list(message):
	email_payload = message.get_payload()
	if message.is_multipart():
		email_messages = list(_get_email_messages(email_payload))
	else:
		email_messages = [email_payload]
	return email_messages

def _get_email_messages(email_payload):
	for msg in email_payload:
		if isinstance(msg, (list,tuple)):
			for submsg in _get_email_messages(msg):
				yield submsg
		elif msg.is_multipart():
			for submsg in _get_email_messages(msg.get_payload()):
				yield submsg
		else:
			yield msg

def print_dict(obj):
	for k,v in obj.items():
		print(f"{k}: {v}")

def _read_email_text(msg):
	content_type = 'NA' if isinstance(msg, str) else msg.get_content_type()
	encoding = 'NA' if isinstance(msg, str) else msg.get('Content-Transfer-Encoding', 'NA')
	if 'text/plain' in content_type and 'base64' not in encoding:
		msg_text = msg.get_payload()
	# elif 'text/html' in content_type and 'base64' not in encoding:
	#     msg_text = get_html_text(msg.get_payload())
	# elif content_type == 'NA':
	#     msg_text = get_html_text(msg)
	else:
		msg_text = None
	return (content_type, encoding, msg_text)

if __name__ == "__main__":
	main(sys.argv[1:])