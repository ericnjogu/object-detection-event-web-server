from flask import Flask, request
from flask.wrappers import Response
import argparse
import grpc
from concurrent import futures
import logging
import redis
from flask_compress import Compress
import os
from io import StringIO
import google.protobuf.json_format as json_format

from proto.generated import detection_handler_pb2_grpc, detection_handler_pb2
import web_handler

# the react app and web streaming app will appear to run from the same host but different ports
ENV_VAR_NETWORK_HOST = 'STREAMING_NETWORK_HOST'
network_host = os.environ.get(ENV_VAR_NETWORK_HOST, 'localhost')

app = Flask(__name__)
# to be set on IDE run config, shell or other way
app.config.from_envvar('SETTINGS')
Compress(app)

# pubsub variable so that it can be initialized in __main__()
pubsub = None


def detection_event_stream():
    """ get available detection item in channel """
    try:
        buffer = StringIO()
        message_count = 0
        while True:
            message = pubsub.get_message()
            if message is None:
                break
            else:
                data = message.get('data');
                protobuf_request = detection_handler_pb2.handle_detection_request()
                if isinstance(data, bytes):
                    protobuf_request.ParseFromString(data)
                else:
                    continue
                path = web_handler.save_frame_to_redis(protobuf_request, redis)
                web_handler.clear_frame_set_path(protobuf_request, path)
                json_no_newlines = json_format.MessageToJson(protobuf_request).replace('\n', '')
                http_event = f"event:detection\ndata:{json_no_newlines}\nid:{protobuf_request.string_map['id']}\n\n"
                # https://stackoverflow.com/a/1686400/315385
                buffer.write(http_event)
                message_count += 1
        logging.debug(f"retrieved {message_count} messages from redis")
        return buffer.getvalue()
    except redis.exceptions.ConnectionError:
        pass


@app.route('/stream')
def stream():
    response = Response(detection_event_stream(), mimetype="text/event-stream")
    # TODO retrieve/manage access scheme
    response.headers.add('Access-Control-Allow-Origin', f'http://{network_host}:{3000}')

    return response


@app.route(f'{web_handler.FRAMES_ROUTE}/<img_key>')
def frames(img_key):
    frame = redis.get(request.path)
    if frame is None:
        response = Response(f'{img_key} not found', status=404)
    else:
        response = Response(frame, mimetype="image/jpeg")

    return response


if __name__ == '__main__':
    logging.getLogger().setLevel(logging.DEBUG)
    # parse args
    parser = argparse.ArgumentParser(description=" stream detected object events to web clients")
    parser.add_argument("prediction_channel", help="channel to subscribe to for detection handling requests")
    args = parser.parse_args()

    # connect to redis at default port, host as these will be wired up to the container
    redis = redis.Redis()
    pubsub = redis.pubsub()
    channel = args.prediction_channel
    pubsub.subscribe(channel)

    # start flask
    app.debug = True
    app.run(host=network_host)
