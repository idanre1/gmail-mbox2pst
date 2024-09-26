#!/bin/bash
sudo apt update
sudo apt install dovecot-imapd dovecot-pop3d
sudo systemctl disable dovecot
sudo systemctl stop dovecot
# https://doc.dovecot.org/2.3/configuration_manual/mail_location/mbox/
# https://doc.dovecot.org/2.3/configuration_manual/mail_location/mbox/mboxchildfolders/
sudo sh -c "echo 'mail_location = mbox:~/mail:LAYOUT=maildir++:INDEX=~/mail/index:CONTROL=~/mail/control:UTF-8:BROKENCHAR=_' >> /etc/dovecot/dovecot.conf"
mkdir -p ~/mail
