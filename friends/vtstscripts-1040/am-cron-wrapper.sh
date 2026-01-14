#!/bin/bash -l

if [[ ! -d $1 ]]; then
    echo "$1 is not a directory"
    exit 1
fi

cd $1
automagician.py -rb
