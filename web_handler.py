import numpy
import logging

from proto.generated import detection_handler_pb2_grpc, detection_handler_pb2


class WebDetectionHandler(detection_handler_pb2_grpc.DetectionHandlerServicer):
    def __init__(self, queue):
        self.queue = queue

    def handle_detection(self, request, context):
        """
        handle a detection output
        """
        frame = numpy.array(request.frame.numbers).reshape(request.frame.shape)
        # save image to buffer or temporary file location
        self.queue.put(request)
        logging.info(f'placed request on queue, frame_count: {request.frame_count}')
        return detection_handler_pb2.handle_detection_response(status=True)
