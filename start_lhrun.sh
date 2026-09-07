#!/bin/bash
while true; do
    echo "Starting localhost.run tunnel..."
    ssh -R 80:localhost:8080 -o StrictHostKeyChecking=no nokey@localhost.run > lhrun.log 2>&1
    echo "Tunnel closed. Restarting in 3 seconds..."
    sleep 3
done
