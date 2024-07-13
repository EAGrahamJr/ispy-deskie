# Source this file to get shell aliases
#alias spinstall='sudo cp /home/crackers/*.service /etc/systemd/user/'
#alias sysr='systemctl --user daemon-reload'
#alias syslinger='loginctl enable-linger'

#alias sparkle='systemctl --user start nightlight.service'
#alias spstop='systemctl --user stop nightlight.service'
#alias spstat='systemctl --user status nightlight.service'
#alias spenable='systemctl --user enable nightlight.service'
#alias spdisable='systemctl --user disable nightlight.service'

#!/bin/bash

# Check if the command-line parameter is provided
if [ $# -eq 0 ]; then
    echo "No arguments provided"
    exit 1
fi

# Parse the command-line parameter
case "$1" in
    install)
        sudo cp $2.service /etc/systemd/user/

        systemctl --user daemon-reload
        systemctl --user start $2.service
        systemctl --user enable $2.service
        loginctl enable-linger

        echo "Service $2 installed successfully"
        ;;
    stop)
        systemctl --user stop $2.service
        echo "Service $2 stopped successfully"
        ;;
    start)
        systemctl --user start $2.service
        echo "Service $2 started successfully"
        ;;
    status)
        systemctl --user status $2.service
        ;;
    enable)
        systemctl --user enable $2.service
        echo "Service $2 enabled successfully"
        ;;
    disable)
        systemctl --user disable $2.service
        echo "Service $2 disabled successfully"
        ;;
    *)
        echo "Invalid argument"
        exit 1
        ;;
esac

exit 0
