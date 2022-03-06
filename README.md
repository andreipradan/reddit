# reddit
Send Reddit live thread updates to telegram

### Installation
```
git clone git@github.com:andreipradan/reddit.git
cd reddit
poetry install
poetry run websocket  # starting the websocket
```

### Local automatic deployments on raspberry pi

#### Steps
1. Create your new service
```
sudo nano /etc/systemd/system/reddit.service
```

2. Paste the following contents into the `reddit.service` file
```
[Unit]
Description=Reddit live thread to telegram

[Service]
User=pi
WorkingDirectory=/home/pi/projects/reddit
ExecStart=/home/pi/.poetry/bin/poetry run websocket
Restart=always


[Install]
WantedBy=multi-user.target
```

3. Reload the service files to include the new service.

`sudo systemctl daemon reload`
4. Start your service

`sudo systemctl start reddit.service`
5. Check service status

`sudo systemctl status reddit.service`
6. Setup and start [ngrok](https://ngrok.com/) on port 7777

`ngrok http 7777`

7. Add [a new github webhook](https://github.com/andreipradan/reddit/settings/hooks/) (you might need to fork this repo)
8. Add your public URL provided by ngrok as the Payload URL with the `/github/` suffix
e.g. if ngrok provides this url `https://abcd-efgh-ijkl.ngrok.io` the Payload URL will be `https://abcd-efgh-ijkl.ngrok.io/github/`
9. Start the Fastapi web server that listens to the github webhook requests
10. Enjoy!
