from flask import Flask
from flask.wrappers import Response
import argparse
import grpc
from concurrent import futures
import logging
import queue

from proto.generated import detection_handler_pb2_grpc
from web_handler import WebDetectionHandler

app = Flask(__name__)
queue = queue.SimpleQueue()

def detection_event_stream():
    """ get available detection item in event queue """
    yield queue.get()

@app.route('/stream')
def stream():
    return Response(detection_event_stream(), mimetype="text/event-stream")

if __name__ == '__main__':
    # start grpc server
    parser = argparse.ArgumentParser(description=" stream detected object events to web clients")
    parser.add_argument("handler_port", help="port to listen for detection handling requests")
    args = parser.parse_args()
    # credit - https://www.semantics3.com/blog/a-simplified-guide-to-grpc-in-python-6c4e25f0c506/
    # create server
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    # add implementing class to server
    web_handler = WebDetectionHandler(queue)
    detection_handler_pb2_grpc.add_DetectionHandlerServicer_to_server(web_handler, server);
    # listen
    port = args.handler_port
    logging.getLogger().setLevel(logging.DEBUG)
    logging.info(f'starting server on port {port}')
    server.add_insecure_port(f'[::]:{port}')
    server.start()

    # start flask
    app.debug = True
    app.run(threaded=True)
