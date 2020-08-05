#!/usr/bin/env bash

# Invoke with one of the following commands:
#   ./benchmark.sh > stdout.txt 2> stderr.txt                    # To redirect do different files.
#   ./benchmark.sh > both.txt 2>&1                               # To redirect to the same file
#   ./benchmark.sh > >(tee stdout.log) 2> >(tee stderr.log >&2)  # To see output on console at same time.
#
# References:
# - https://stackoverflow.com/questions/7526971/how-to-redirect-both-stdout-and-stderr-to-a-file
# - https://stackoverflow.com/questions/692000/how-do-i-write-stderr-to-a-file-while-using-tee-with-a-pipe
# - https://stackoverflow.com/questions/3737740/is-there-a-better-way-to-run-a-command-n-times-in-bash

set -x
N=10
time for ((n=0;n<$N;n++)) ; do snmpwalk -u secureUser  -l authPriv -a MD5 -x DES -A auth_key -X priv_key 192.168.1.23 1.3.6.1.2 ; done
time for ((n=0;n<$N;n++)) ; do snmpwalk -u secureUser2 -l authPriv -a MD5 -x AES -A auth_key -X priv_key 192.168.1.23 1.3.6.1.2 ; done
time for ((n=0;n<$N;n++)) ; do snmpwalk -u secureUser3 -l authPriv -a SHA -x AES -A auth_key -X priv_key 192.168.1.23 1.3.6.1.2 ; done
time for ((n=0;n<$N;n++)) ; do snmpwalk -u secureUser4 -l authPriv -a SHA -x DES -A auth_key -X priv_key 192.168.1.23 1.3.6.1.2 ; done
