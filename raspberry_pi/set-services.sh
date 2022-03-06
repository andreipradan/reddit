#!/bin/bash
set -euo
echo "pi ALL=(ALL) NOPASSWD: /usr/bin/systemctl restart reddit.service" >> /etc/sudoers.d/pi
cp raspberry_pi/services/fastapi.service /etc/systemd/system
cp raspberry_pi/services/ngrok.service /etc/systemd/system
cp raspberry_pi/services/reddit.service /etc/systemd/system
echo "Copied services files to systemd"
systemctl daemon-reload
systemctl start fastapi.service
systemctl start ngrok.service
systemctl start reddit.service
