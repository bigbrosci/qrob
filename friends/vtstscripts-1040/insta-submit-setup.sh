#!/bin/bash -l                                                                                                                                                                                              

TMPFILE=automagician-insta-submit-$(date +%s)
crontab -l > $TMPFILE
echo "* * * * * $(which insta-submit.sh)" >> $TMPFILE
crontab $TMPFILE
rm $TMPFILE
