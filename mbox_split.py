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

	mcount = mjunk = mchat = msaved = 0

	def decode(s):
		# https://stackoverflow.com/questions/7331351/python-email-header-decoding-utf-8
		# https://www.base64decode.org/
		try:
			result = str(make_header(decode_header(s)))
		except:
			print("Error decoding header: " + s)
			dh=decode_header(s)
			print("Decode: " + str(dh))
			l=[]
			for hdr,enc in dh:
				if (enc == 'iso-8859-8-i'):
					enc='iso-8859-8'
				l.append((hdr,enc))
			h=make_header(l)
			print("Make header:" + str(h))
		return result

	print("Looping:")
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
			else:
				for label in gmail_labels:
					# ignore meta labels
					if label in ["Important","Unread","Starred","Newsletters"]:
						continue
					if label in ["חשוב","לא נקרא","נפתח","קטגוריה – אישי", "קטגוריה – עדכונים", "קטגוריה – קידומי מכירות","קטגוריה – רשתות חברתיות"]:
						continue

					# use first match
					tbox = label

					# handle odd labels
					if label == "[Imap]/Archive":
						tbox = "Archive"
					elif label == "מאוחסן בארכיון":
						tbox = "Archive"
					break
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
			print("Error decoding From: " + message["From"])
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
			import chardet
			print("Error adding message to mbox: " + tbox)
			print("Message: " + message)
			print("From: " + mfrom)
			print("Message ID: " + mid)
			print("Fallback to ascii(ignore) encoding")
			msg=str(msg, chardet.detect(message)['encoding']).encode('ascii', 'ignore')
			boxes[tbox].add(msg)


	print(str(mcount) + " messages processed, " + str(msaved) + " messages saved")
	print("ignored: " + str(mjunk) + " spam, " + str(mchat) + " mchat")
	print("File originally contained " + str(sourcembox.__len__()) + " messages to process")

if __name__ == "__main__":
    main(sys.argv[1:])