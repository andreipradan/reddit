#!/bin/bash
set -euo
systemctl daemon-reload
systemctl start fastapi.service ngrok.service reddit.service
systemctl enable fastapi.service ngrok.service reddit.service
