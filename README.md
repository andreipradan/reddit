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
`poetry run full-setup`

What happens in the background:
1. Copies the reddit, ngrok and fastapi service files from /deploy/services into /etc/systemd/system
2. Reloads the service files to include the new services.
3. Starts the new services
4. Add [a new github webhook](https://github.com/andreipradan/reddit/settings/hooks/) (you might need to fork this repo)
5. Add your public URL provided by ngrok as the Payload URL with the `/github/` suffix
e.g. if ngrok provides this url `https://abcd-efgh-ijkl.ngrok.io` the Payload URL will be `https://abcd-efgh-ijkl.ngrok.io/github/`
6. Start the Fastapi web server that listens to the github webhook requests
7. Enjoy!

You can check your status by doing `deploy/show-logs.sh`
