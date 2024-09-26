Convert your Gmail (Google takeout) MBOX to PST file
===
# MBOX2PST TLDR
- Use google takeout to have a single MBOX file
- Split mbox by gmail tags
- Use dovecot as an IMAP server under wsl
- Use smtp4dev as a dummy smtp server (New Outlook must have sucessfull SMTP test for IMAP to work)
- Use outlook to fetch all IMAP folders
- Use outlook to export PST file (File->Export)
# Gmail MBOX split with labels
Split MBOX by labels  
Please put inputfile on other path
```bash
./mbox_to_maildir.sh
```
# Install dovecot under WSL
```bash
./install_dovecot.sh
```
# Install smtp4dev
- Goto https://github.com/rnwood/smtp4dev
- Download "Windows x64 binary standalone - Desktop app edition" and unzip
- Configure other IMAP port for prevent collision with dovecot
- Run it Before configuring outlook
# Convert
### Service dovecot under WSL
```
# Start dovecot
sudo systemctl start dovecot
# subscribe all subfolders to IMAP
python subscribe.py ~/mail
```
### Register dovecot in outlook
- Control Panel -> Mail -> Configure IMAP on 127.0.0.1
- Open outlook and make coffee
# Uninstall
```sh
sudo systemctl stop dovecot
rm ~/mail/*
```