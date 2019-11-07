import numpy
import logging
import queue
import google.protobuf.json_format as json_format

from proto.generated import detection_handler_pb2_grpc, detection_handler_pb2


class WebDetectionHandler(detection_handler_pb2_grpc.DetectionHandlerServicer):
    def __init__(self):
        # create queue
        self.queue = queue.SimpleQueue()

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
