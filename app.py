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

from proto.generated import detection_handler_pb2_grpc, detection_handler_pb2
from web_handler import WebDetectionHandler
import web_handler

# the react app and web streaming app will appear to run from the same host but different ports
ENV_VAR_NETWORK_HOST = 'STREAMING_NETWORK_HOST'
network_host = os.environ.get(ENV_VAR_NETWORK_HOST, 'localhost')

app = Flask(__name__)
# to be set on IDE run config, shell or other way
app.config.from_envvar('SETTINGS')
Compress(app)
# connect to redis at default port, host as these will be wired up to the container
redis = redis.StrictRedis()
pubsub = redis.pubsub()
CHANNEL = "detection_events"
pubsub.subscribe(CHANNEL)


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
                # https://stackoverflow.com/a/1686400/315385
                buffer.write(data.decode() if isinstance(data, bytes) else '')
                message_count += 1
        logging.debug(f"retrieved {message_count} messages from redis:")
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
    # parse args
    parser = argparse.ArgumentParser(description=" stream detected object events to web clients")
    parser.add_argument("handler_port", help="port to listen for detection handling requests")
    args = parser.parse_args()
    # credit - https://www.semantics3.com/blog/a-simplified-guide-to-grpc-in-python-6c4e25f0c506/
    # create server
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    # grpc port setup
    port = args.handler_port
    logging.getLogger().setLevel(logging.DEBUG)
    logging.info(f'starting server on port {port}')
    server.add_insecure_port(f'[::]:{port}')
    # add implementing class to server
    web_handler = WebDetectionHandler(redis, CHANNEL)
    detection_handler_pb2_grpc.add_DetectionHandlerServicer_to_server(web_handler, server);
    # start grpc server
    server.start()

    # start flask
    app.debug = True
    app.run(host=network_host)
