from flask import Flask
from flask.wrappers import Response
import argparse
import grpc
from concurrent import futures
import logging
import queue
import google.protobuf.json_format as json_format

from proto.generated import detection_handler_pb2_grpc, detection_handler_pb2
from web_handler import WebDetectionHandler

app = Flask(__name__)
event_queue = None

def detection_event_stream():
    """ get available detection item in event queue """
    yield json_format.MessageToJson(event_queue.get())

@app.route('/stream')
def stream():
    response = Response(detection_event_stream(), mimetype="text/event-stream")
    # TODO manage this via configuration
    response.headers.add('Access-Control-Allow-Origin', 'http://localhost:3000')
    return response

if __name__ == '__main__':
    # start grpc server
    parser = argparse.ArgumentParser(description=" stream detected object events to web clients")
    parser.add_argument("handler_port", help="port to listen for detection handling requests")
    parser.add_argument("--testing", help="add some test items to the event queue on startup", action="store_true")
    args = parser.parse_args()
    # credit - https://www.semantics3.com/blog/a-simplified-guide-to-grpc-in-python-6c4e25f0c506/
    # create server
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    # add implementing class to server
    web_handler = WebDetectionHandler(event_queue)
    detection_handler_pb2_grpc.add_DetectionHandlerServicer_to_server(web_handler, server);
    # listen
    port = args.handler_port
    logging.getLogger().setLevel(logging.DEBUG)
    logging.info(f'starting server on port {port}')
    server.add_insecure_port(f'[::]:{port}')
    server.start()
    # setup queue
    event_queue = queue.SimpleQueue()
    if args.testing is True:
        event_queue.put(detection_handler_pb2.handle_detection_request(
            start_timestamp=1106,
            detection_classes=[3],
            detection_scores=[.8],
            detection_boxes=detection_handler_pb2.float_array(numbers=[1, 2, 3, 4], shape=[1, 4]),
            instance_name='testing',
            frame=detection_handler_pb2.float_array(numbers=[1, 2, 3, 3, 4, 5], shape=[2,3]),
            frame_count=1110,
            source="code",
            float_map={"frame_height": 400, "frame_width": 400}))

    # start flask
    app.debug = True
    app.run(threaded=True)
