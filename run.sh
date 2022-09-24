#! /bin/bash

# Restart 'python main.py' every time remote repo updated

su

restart_process() {
    echo 'LOG | Restarting process'
    sudo kill $FOO_PID || true
    python ./main.py &
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
