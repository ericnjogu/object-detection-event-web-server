import numpy
import logging
import google.protobuf.json_format as json_format

from proto.generated import detection_handler_pb2_grpc, detection_handler_pb2


def frame_array_to_canvas_image_data(frame):
    """
    Takes image array and adds an alpha channel to each pixel
    :param frame: a flattened array that represents a video frame (image)
    :return: a flattened array in a format ready to be used by HTML5 ImageData
    """
    # TODO change this to use dataframe and compare performance. Current is 0.96s for ./samples/detection-request-with-frame-01.bin
    # discard the openCV outer array from the shape, change to int
    numpy_array = numpy.array(frame.numbers, dtype=numpy.int32).reshape(frame.shape)
    alpha_array = []
    for row in numpy_array:
        for col in row:
            alpha_array.append(numpy.append(col, 255))
    return numpy.array(alpha_array).ravel().tolist()


def merge_request_with_canvas_image_data(request, canvas_data):
    """
    :param request: a protobuf message of type detection_handler_pb2.handle_detection_request
    :param canvas_data: a flattened array with image data in the form expected by HTML5 ImageData
    :return: the request, with frame.numbers replaced by the canvas_data
    """
    frame_request = detection_handler_pb2.handle_detection_request(
        frame=detection_handler_pb2.float_array(numbers=canvas_data))
    request.ClearField('frame')
    request.MergeFrom(frame_request)

    return request


class WebDetectionHandler(detection_handler_pb2_grpc.DetectionHandlerServicer):
    def __init__(self, redis, channel):
        self.redis = redis
        self.channel = channel

    def handle_detection(self, request, context):
        """
        handle a detection output
        """
        img_data = frame_array_to_canvas_image_data(request.frame)
        merged_req = merge_request_with_canvas_image_data(request, img_data)
        json_no_newlines = json_format(merged_req)
        # can send extra data line with modified frame,
        # how do I delete the one in the original request to avoid sending unnecessary data
        http_event = f"event:detection\ndata:{json_no_newlines}\n\n"
        self.redis.publish(self.channel, http_event)
        logging.info(f'placed request on queue, frame_count: {request.frame_count}')
        return detection_handler_pb2.handle_detection_response(status=True)
