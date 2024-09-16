#!/usr/bin/env python

# Adapted from:
# http://wboptimum.com/splitting-gmail-mbox-by-label/

import sys
import getopt
import mailbox

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
		"Archive":	mailbox.mbox(prefix + "Archive", create=True)
	}

	sourcembox = mailbox.mbox(in_mbox, create=False)
	print(str(sourcembox.__len__()) + " messages to process")
	sys.stdout.flush()

	mcount = mjunk = mchat = msaved = 0
	for message in sourcembox:
		read = True
		flagged = False
		mcount += 1
		gmail_labels = message["X-Gmail-Labels"]
		tbox = "Archive"				# default target box: Archive

		if gmail_labels:
			gmail_labels = gmail_labels.split(',')	# from here we only work on an array to avoid partial matches
			# handle flags
			if "Unread" in gmail_labels:
				read = False
			if "Starred" in gmail_labels:
				flagged = True

			# order matters!
			if "Spam" in gmail_labels:		# skip all spam
				mjunk += 1
				continue
			elif "Chat" in gmail_labels:		# skip all chat
				mchat += 1
				continue
			elif "Sent" in gmail_labels:		# anything that has Sent goes to Sent box
				tbox = "Sent"
			elif "Inbox" in gmail_labels:		# Inbox treated here because some messages can be Sent,Inbox
				tbox = "Inbox"
			else:
				for label in gmail_labels:
					# ignore meta labels
					if label == "Important" or label == "Unread" or label == "Starred" or label == "Newsletters":
						continue

					# use first match
					tbox = label

					# handle odd labels
					if label == "[Imap]/Archive":
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

		mfrom = message["From"] or "Unknown"
		mid = message["Message-Id"] or "<N/A>"
		print("Storing " + mid + " from \"" + mfrom + "\" to mbox \"" + tbox + "\"")
		msaved += 1

		if tbox not in boxes:
			boxes[tbox] = mailbox.mbox(prefix + tbox, create=True)
		boxes[tbox].add(message)

	print(str(mcount) + " messages processed, " + str(msaved) + " messages saved")
	print("ignored: " + str(mjunk) + " spam, " + str(mchat) + " mchat")

if __name__ == "__main__":
    main(sys.argv[1:])