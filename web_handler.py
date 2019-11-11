import numpy
import logging
import google.protobuf.json_format as json_format
import tempfile

from proto.generated import detection_handler_pb2_grpc, detection_handler_pb2


def frame_array_to_image_data(frame):
    """
    Takes image array and adds an alpha channel to each pixel
    :param frame: a flattened array that represents a video frame (image)
    :return: a flattened array in a format ready to be used by HTML5 ImageData
    """
    logging.debug(f"frame shape is {frame.shape}")
    #logging.debug(f"frame numbers: {frame.numbers}")
    # discard the openCV outer array from the shape, change to int
    numpy_array = numpy.array(frame.numbers, dtype=numpy.int32).reshape(frame.shape)
    alpha_array = []
    for row in numpy_array:
        for col in row:
            alpha_array.append(numpy.append(col, 255))
    return numpy.array(alpha_array).ravel().tolist()


class WebDetectionHandler(detection_handler_pb2_grpc.DetectionHandlerServicer):
    def __init__(self, redis, channel):
        self.redis = redis
        self.channel = channel

    def handle_detection(self, request, context):
        """
        handle a detection output
        """
        # save request to file for further testing
        with tempfile.NamedTemporaryFile(mode='w+b', delete=False) as tmp_file:
            msg_to_string = request.SerializeToString()
            #logging.debug(msg_to_string)
            tmp_file.write(msg_to_string)
            logging.debug(f"wrote detection request to {tmp_file.name}")
        frame_request = detection_handler_pb2.handle_detection_request(
            frame=detection_handler_pb2.float_array(numbers=frame_array_to_image_data(request.frame)))
        request.MergeFrom(frame_request)
        json_no_newlines = json_format.MessageToJson(request).replace('\n', '')
        # can send extra data line with modified frame,
        # how do I delete the one in the original request to avoid sending unnecessary data
        http_event = f"event:detection\ndata:{json_no_newlines}\n\n"
        self.redis.publish(self.channel, http_event)
        logging.info(f'placed request on queue, frame_count: {request.frame_count}')
        return detection_handler_pb2.handle_detection_response(status=True)
