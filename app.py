from flask import Flask
from flask.wrappers import Response
import argparse
import grpc
from concurrent import futures
import logging
import redis
from flask_compress import Compress

from proto.generated import detection_handler_pb2_grpc, detection_handler_pb2
from web_handler import WebDetectionHandler

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
        message = pubsub.get_message()
        if message is not None:
            data = message.get('data')
            # redis returns a 1 when there's no data or for the first get,
            # which causes TypeError: 'int' object is not iterable, so converting to string
            if isinstance(data, int):
                return str(data)
            else:
                return data
    except redis.exceptions.ConnectionError:
        pass

@app.route('/stream')
def stream():
    response = Response(detection_event_stream(), mimetype="text/event-stream")
    # TODO manage this via configuration
    response.headers.add('Access-Control-Allow-Origin', 'http://localhost:3000')
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
    app.run(threaded=True)
