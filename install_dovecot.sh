#!/bin/bash
sudo apt update
sudo apt install dovecot-imapd dovecot-pop3d
sudo systemctl stop dovecot
sudo sh -c "echo 'mail_location = mbox:~/mail' >> /etc/dovecot/dovecot.conf"
mkdir -p ~/mail
