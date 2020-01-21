# Video Object Detection Web Events Server
This app implements a gRPC + flask server that takes detection handler requests (the result of video object detection) and streams them via HTTP to web clients.

## Resources
- [One of the answers](https://stackoverflow.com/a/12236019/315385) to `How to implement server push in Flask framework` on stackoverflow.com
- HTTP server events - https://www.html5rocks.com/en/tutorials/eventsource/basics/
- Redis publish/subscribe - https://github.com/andymccurdy/redis-py/#publish--subscribe

## Running
- Download or clone the [video object detection repo](https://github.com/kunadawa/video-object-detection)
- when started this flask app will listen to a redis channel which the predition results are being published to. The name of the channel is given on the CLI as an arg and should match the one given to the app generating the prediction results.
- In this repo's root, make the following soft link to the generated protobuf code (check the repos readme.md for instructions on how to generate the code)

  `[video object detection repo]/proto`

- Run the basic startup script
  `bash start.sh <redis-channel-name>`

##### OR (step by step commands)
- add the generated python code to the python path

   `export PYTHONPATH=.:[video object detection repo]proto/generated/`
- set an environmental variable for the flask app settings

    `export SETTINGS=settings.cfg`
- if running on a network (not localhost), set host name where the react app is running. This will help to avoid CORS errors.

 `export STREAMING_NETWORK_HOST=192.168.100.55`

- startup the server with a command such as the one below

  `python app.py 50002 <redis-channel-name>`

## Testing
Individual tests can be run like this:

`bash run_with_env.sh pytest web_handler_test.py --disable-warnings --log-cli-level=DEBUG`

## Contributors
Eric Njogu

## License
MIT
