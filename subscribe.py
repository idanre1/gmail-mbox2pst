import os
from pathlib import Path

# add arg for path
import argparse
parser = argparse.ArgumentParser()
parser.add_argument("path", help="Path to the maildir")
args = parser.parse_args()

# env var $USER
usr = os.getenv('USER')

# cmd
cmd_=f"doveadm mailbox subscribe -u {usr}"

# find all files starting with '.'
root = Path(args.path)
for f_ in root.glob('.*'):
    # remove leading '.'
    f = str(f_)[1:]

    # cmd
    cmd = f"{cmd_} '{f}'"
    
    # execute cmd
    print(f"Processing {f}")
    os.system(cmd)


