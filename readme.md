# Video Object Detection Web Events Server
This app implements a gRPC + flask server that takes detection handler requests (the result of video object detection) and streams them via HTTP to web clients.

## Resources
- [One of the answers](https://stackoverflow.com/a/12236019/315385) to `How to implement server push in Flask framework` on stackoverflow.com
- HTTP server events - https://www.html5rocks.com/en/tutorials/eventsource/basics/
- Redis publish/subscribe - https://github.com/andymccurdy/redis-py/#publish--subscribe

## Redis Notes
When retrieving a message from the pubsub when many have been pushed, there was a redis error (`subscribe scheduled to be closed ASAP for overcoming of output buffer limits`) that caused the connection to be closed. This was resolved by using this configuration in redis.conf - `client-output-buffer-limit pubsub 0 0 0`

## Setup
A conda environment is created to install required packages.
 - Run `conda env create -f env.yaml` to setup a conda environment

## Running
- Run the basic startup script
  `bash start.sh <redis-channel-name>`

##### OR (step by step commands)
- set an environmental variable for the flask app settings

    `export SETTINGS=settings.cfg`
- if running on a network (not localhost), set host name where the react app is running. This will help to avoid CORS errors.

 `export STREAMING_NETWORK_HOST=192.168.100.55`

- startup the server with a command such as the one below

  `python app.py 50002 <redis-channel-name>`

## Testing
Individual tests can be run like this:

`bash run_with_env.sh python -m pytest web_handler_test.py --disable-warnings --log-cli-level=DEBUG`

## Contributors
Eric Njogu

## License
MIT
