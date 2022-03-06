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
`sudo raspberry-pi/setup-continuous-deployment.sh`

What happens in the background:
1. Copies the reddit, ngrok and fastapi service files from /raspberry-pi into /etc/systemd/system
2. Reloads the service files to include the new services.
3. Starts the new services

You can check your status by doing

```
sudo systemctl status fastapi.service
sudo systemctl status ngrok.service
sudo systemctl status reddit.service
```

8. Add [a new github webhook](https://github.com/andreipradan/reddit/settings/hooks/) (you might need to fork this repo)
9. Add your public URL provided by ngrok as the Payload URL with the `/github/` suffix
e.g. if ngrok provides this url `https://abcd-efgh-ijkl.ngrok.io` the Payload URL will be `https://abcd-efgh-ijkl.ngrok.io/github/`
10. Start the Fastapi web server that listens to the github webhook requests
11. Enjoy!
