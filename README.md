Convert your Gmail MBOX (Google takeout) to PST file
===
# tldr
- Use google takeout to have a single MBOX file
- Use dovecot as an IMAP server under wsl
- Use smtp4dev as a dummy smtp server (New Outlook must have sucessfull SMTP test for IMAP)
- Convert mbox to maildir format
- Use outlook to fetch all IMAP folders
- Use outlook to export pst file
# dovecot
```bash
./install_dovecot.sh
```
# GMail MBOX to Maildir format with labels
Split MBOX by labels  
Please put inputfile on other path
```bash
./mbox_to_maildir.sh
```
