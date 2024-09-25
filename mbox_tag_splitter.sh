#!/bin/bash
# filename should be absolute path
filename=`realpath $1`
# script path
script_path=`readlink -f "${BASH_SOURCE:-$0}"`
script_path=`dirname $script_path`

# Create maildir path
cd ~/mail
# Split mbox by folders
python $script_path/mbox_split.py --infile $filename
# Convert mbox to maildir
# ./mb2md.pl -s ~/path/to/split_Inbox.mbox -d ~/path/to/output/Inbox
