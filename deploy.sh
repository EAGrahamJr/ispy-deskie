#!/usr/bin/env sh

#DEST="murphy.local:/home/crackers/projects/murphy-control"
#rsync -avz --delete *.py $DEST
#rsync -avz --delete *.service $DEST
#rsync -avz --delete systemd.sh $DEST
cp *.py CIRCUITPY/
mv CIRCUITPY/the_code.py CIRCUITPY/code.py

