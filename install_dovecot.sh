#!/bin/bash
sudo apt update
sudo apt install dovecot-imapd dovecot-pop3d
sudo systemctl stop dovecot
# https://doc.dovecot.org/2.3/configuration_manual/mail_location/mbox/
sudo sh -c "echo 'mail_location = mbox:~/mail' >> /etc/dovecot/dovecot.conf"
mkdir -p ~/mail
