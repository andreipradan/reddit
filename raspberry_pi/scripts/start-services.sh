#!/bin/bash
set -euo
systemctl daemon-reload
systemctl start fastapi.service
systemctl start ngrok.service
systemctl start reddit.service
