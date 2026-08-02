#!/usr/bin/env sh

# very simple "deploy everything" script, with a slight "delay" to activate the application
# assumes the device mount point is `ln -s` to CIRCUITPY locally

cp *.py CIRCUITPY/
mkdir CIRCUITPY/fonts
cp WS_Regular-14.bdf CIRCUITPY/fonts

# settings if exists
if [[ - f settings.toml ]]; then
    cp settings.toml CIRCUITPY
fi

# wait a sec before "restarting" - this is to ensure everything is sync'd
echo "Sleeping for sync"
sleep 5
mv CIRCUITPY/the_code.py CIRCUITPY/code.py
