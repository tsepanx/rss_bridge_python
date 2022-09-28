#! /bin/bash

# Restart 'run.sh' every time remote repo updated

sudo echo

restart_process() {
    echo 'LOG | Restarting process'
    sudo kill -9 "$FOO_PID" 2>/dev/null

    pip install -r requirements.txt
    /bin/bash ./run.sh &

    FOO_PID=$!
    echo 'LOG | Started process'
}


restart_process
while true; do
    echo 'LOG | Git pull'
    if [[ $(git pull) != 'Already up to date.' ]]; then
        restart_process
    else
        sleep 5
    fi
done
