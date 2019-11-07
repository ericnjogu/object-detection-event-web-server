import numpy
import logging
import queue
import google.protobuf.json_format as json_format
from flask import Flask
from flask.wrappers import Response
import grpc
from concurrent import futures

from proto.generated import detection_handler_pb2_grpc, detection_handler_pb2


class WebDetectionHandler(detection_handler_pb2_grpc.DetectionHandlerServicer, Flask):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # create queue
        self.queue = queue.SimpleQueue()
        # setup routing
        self.add_url_rule('/stream', view_func=self.stream)

    def start_grpc_server(self, handler_port):
        # credit - https://www.semantics3.com/blog/a-simplified-guide-to-grpc-in-python-6c4e25f0c506/
        # create server
        grpc_server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        # grpc port setup
        logging.getLogger().setLevel(logging.DEBUG)
        logging.info(f'starting GRPC server on port {handler_port}')
        grpc_server.add_insecure_port(f'[::]:{handler_port}')
        detection_handler_pb2_grpc.add_DetectionHandlerServicer_to_server(self, grpc_server);
        # start grpc server
        grpc_server.start()

    def stream(self):
        response = Response(self.detection_event_stream(), mimetype="text/event-stream")
        # TODO manage this via configuration
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:3000')
        return response

    def handle_detection(self, request, context):
        """
        handle a detection output
        """
        frame = numpy.array(request.frame.numbers).reshape(request.frame.shape)
        # save image to buffer or temporary file location
        self.queue.put(request)
        logging.info(f'placed request on queue, frame_count: {request.frame_count}, queue length: {self.queue.qsize()}, '
                     f'id {id(self.queue)}, handler id {id(self)}')
        return detection_handler_pb2.handle_detection_response(status=True)

    def detection_event_stream(self):
        """ get available detection item in event queue """
        # json_format or a dependency appears to change top level field names to camel case
        logging.debug(f"event stream request queue size: {self.queue.qsize()}, queue id {id(self.queue)},"
                      f" handler id {id(self)}")
        if not self.queue.empty():
            json_no_newlines = json_format.MessageToJson(self.queue.get()).replace('\n', '')
            return f"event:detection\ndata:{json_no_newlines}\n\n"