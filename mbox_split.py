#!/usr/bin/env python

# Adapted from:
# http://wboptimum.com/splitting-gmail-mbox-by-label/

import sys
import getopt
import mailbox
from email.header import decode_header, make_header

# Multilanguage support for labels
inbox_labels = ["Inbox","תיבת דואר נכנס", "קטגוריה – אישי"]
sent_labels = ["Sent","דואר יוצא"]
archive_labels = ["Archive","מאוחסן בארכיון","[Imap]/Archive"]
spam_labels = ["Spam"]
chat_labels = ["Chat"]
trash_labels = ["Trash","אשפה"]
unread_labels = ["Unread","לא נקרא"]
opened_labels = ["Opened","נפתח"]
important_labels = ["Important","חשוב"]
starred_labels = ["Starred"]
newsletters_labels = ["Newsletters"]
categorized_labels = ["קטגוריה – עדכונים", "קטגוריה – קידומי מכירות","קטגוריה – רשתות חברתיות"] # TODO find english names

def main(argv):
	in_mbox = "source.mbox"
	try:
		opts, args = getopt.getopt(argv, "i:", ["infile="])
	except getopt.GetoptError:
		print("python mbox_split.py -i <infile>")
		sys.exit(2)

	for opt, arg in opts:
		if opt in ("-i", "--infile"):
			in_mbox = arg

	print(f'Processing file "{in_mbox}"')
	sys.stdout.flush()

	# Create common mailboxes
	boxes = {
		"Inbox":	create_mbox("INBOX"),
		"Sent":		create_mbox("Sent"),
		"Archive":	create_mbox("Archive"),
		"Spam":	    create_mbox("Spam"),
		"Chat":	    create_mbox("Chat"),
		"Trash":	create_mbox("Trash"),
	}

	sourcembox = mailbox.mbox(in_mbox, create=False)
	sys.stdout.flush()

	mcount = mjunk = mchat = msaved = missues = merr_cont = 0

	print("Looping:")
	labels={}
	for message in sourcembox:
		read = True
		flagged = False
		mcount += 1
		gmail_labels = message["X-Gmail-Labels"]

		tbox = "Archive" # default target box: Archive
		if gmail_labels:
			gmail_labels = decode(gmail_labels)
			gmail_labels = gmail_labels.split(',')	# from here we only work on an array to avoid partial matches
			# handle flags
			if ab_intersected(unread_labels,gmail_labels):
				read = False
			if ab_intersected(opened_labels,gmail_labels):
				read = True
			if ab_intersected(starred_labels,gmail_labels):
				flagged = True

			# order matters!
			if ab_intersected(spam_labels,gmail_labels):
				mjunk += 1
				tbox = "Spam"
			elif ab_intersected(chat_labels,gmail_labels):
				mchat += 1
				tbox = "Chat"
			elif ab_intersected(trash_labels,gmail_labels):
				tbox = "Trash"
			elif ab_intersected(sent_labels,gmail_labels):
				tbox = "Sent"
			else:
				meta_labels = unions([inbox_labels,archive_labels,important_labels,starred_labels,newsletters_labels,categorized_labels,unread_labels, opened_labels])
				custome_labels = list(set(gmail_labels) - set(meta_labels))

				if (len(custome_labels) > 0):
					# Custome labels
					label = custome_labels[0] # use first match
					# label=label_.replace('/','__') # Handle sublabels in gmail
					if label not in labels:
						labels[label] = 1
					else:
						labels[label] += 1
					# Assign the label
					tbox = label

				elif ab_intersected(inbox_labels,gmail_labels):
					# Inbox treated here because some messages can be Sent,Inbox
					tbox = "Inbox"
				elif ab_intersected(archive_labels,gmail_labels):
					# Archive is last priority
					tbox = "Archive"
				
				# if nothing matched we'll use default set at message loop start

		# fixup missing status flags in the message
		if read:
			message["Status"] = "RO"
		else:
			message["Status"] = "O"
		if flagged:
			message["X-Status"] = "F"

		# try:
		# 	mfrom = decode(message["From"]) or "Unknown"
		# except:
		# 	print("Error decoding From: " + message["From"])
		# 	merr_hdr += 1
		# 	mfrom = "Unknown"
		# mid = message["Message-Id"] or "<N/A>"
		# print("Storing " + mid + " from \"" + mfrom + "\" to mbox \"" + tbox + "\"")
		msaved += 1

		if tbox not in boxes:
			boxes[tbox] = create_mbox(tbox)
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
			issues=False
			for msg in email_messages:
				m=message_encoding_fix(msg)
				# Partial additions
				# try:
				# 	boxes[tbox].add(m)
				# except:
				# 	issues=True
					# print('Error adding message')
					# print(f"Message: {msg}")

			# Add message after in-memory charset adjustments
			try:
				boxes[tbox].add(message)
			except:
				issues=True
			if issues:
				missues += 1
				msaved -= 1

	print(str(mcount) + " messages processed, " + str(msaved) + " messages saved")
	print("Content encoding errors: " + str(merr_cont) + " skipped (even partially): " + str(missues))
	print("File originally contained " + str(sourcembox.__len__()) + " messages to process")
	print("Found " + str(len(labels)) + " unique labels")
	print_dict(labels)

# Helper functions
def create_mbox(name_, raw=False):
	if not raw:
		# label needs to be a folder
		name = f'.{name_}'
		name = name.replace('/','.')
	else:
		name = name_
	print(f"Creating mbox: {name}")
	box = mailbox.mbox(name, create=True)
	return box

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
			# https://stackoverflow.com/questions/77686819/decode-bi-directional-bytes-e-g-iso-8859-8-i-and-iso-8859-8-e-in-python
			# Python lacks support of all ECMA escape characters, shifts, etc
			if (enc == 'iso-8859-8-i'):
				enc='iso-8859-8'
			l.append((hdr,enc))
		result=str(make_header(l))
		# print("Make header:" + str(h))
	return result

def ab_intersected(a,b):
	'''
	Check if two lists have any common elements
	'''
	return not set(a).isdisjoint(b)

def unions(l):
	'''
	Union of multiple lists
	'''
	return list(set().union(*l))

def message_encoding_fix(msg):
	content_type = 'NA' if isinstance(msg, str) else msg.get_content_type()
	encoding = 'NA' if isinstance(msg, str) else msg.get('Content-Transfer-Encoding', 'NA')
	# print(f'{i} - {content_type} - {encoding}')
	fixable_content = ['text/plain', 'multipart/alternative', 'multipart/mixed']
	fixable = ab_intersected(fixable_content,[content_type]) and 'base64' not in encoding
	#print(fixable, content_type, encoding)
	#print(msg)
	if fixable:
		# print(content_type, encoding)
		try:
			# Infer payload charset from Subject charset
			hdr=decode_header(msg['Subject'])
			charset=hdr[0][1]
			if charset is None:
				hdr=decode_header(msg['From'])
				charset=hdr[0][1]
				if charset is None:
					hdr=decode_header(msg['To'])
					charset=hdr[0][1]
			msg.set_charset(charset)
			#print(msg)
		except:
			# print('Error transfering header')
			pass
	return msg

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