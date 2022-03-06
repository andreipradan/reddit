#!/bin/bash
set -euo
cp raspberry_pi/services/fastapi.service /etc/systemd/system
cp raspberry_pi/services/ngrok.service /etc/systemd/system
cp raspberry_pi/services/reddit.service /etc/systemd/system
echo "Done copying services files to /etc/systemd/system"
