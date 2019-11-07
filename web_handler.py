import numpy
import logging
import google.protobuf.json_format as json_format

from proto.generated import detection_handler_pb2_grpc, detection_handler_pb2


class WebDetectionHandler(detection_handler_pb2_grpc.DetectionHandlerServicer):
    def __init__(self, redis, channel):
        self.redis = redis
        self.channel = channel

    def handle_detection(self, request, context):
        """
        handle a detection output
        """
        frame = numpy.array(request.frame.numbers).reshape(request.frame.shape)
        # save image to buffer or temporary file location
        json_no_newlines = json_format.MessageToJson(request).replace('\n', '')
        http_event = f"event:detection\ndata:{json_no_newlines}\n\n"
        self.redis.publish(self.channel, http_event)
        logging.info(f'placed request on queue, frame_count: {request.frame_count}')
        return detection_handler_pb2.handle_detection_response(status=True)
