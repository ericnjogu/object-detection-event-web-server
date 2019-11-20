import numpy
import logging
import google.protobuf.json_format as json_format
import imageio
import io

from proto.generated import detection_handler_pb2_grpc, detection_handler_pb2

FRAMES_ROUTE = '/frames'
FRAME_KEY = 'frame_path'


def save_frame_to_redis(request_id, frame, redis):
    """
    save frame to redis  as jpeg using the request id as a key
    :param request_id: request id
    :param frame: numpy array
    :param redis: redis client
    :return: None
    """
    bytes_io = io.BytesIO()
    imageio.imwrite(bytes_io, frame, format='JPEG-PIL')
    key = f"{FRAMES_ROUTE}/{request_id}.jpg"
    redis.set(key, bytes_io.getvalue())

    return key


def clear_frame_set_path(request, path):
    """
    clear frame field and add an additional entry to string map
    :param request: detection request
    :param path: the path to use to create an entry
    :return: None
    """
    request_to_merge = detection_handler_pb2.handle_detection_request(
        string_map={FRAME_KEY: path})
    request.ClearField('frame')
    request.MergeFrom(request_to_merge)


class WebDetectionHandler(detection_handler_pb2_grpc.DetectionHandlerServicer):
    def __init__(self, redis, channel):
        self.redis = redis
        self.channel = channel

    def handle_detection(self, request, context):
        """
        handle a detection output
        """
        frame = numpy.array(request.frame.numbers, dtype=numpy.uint8).reshape(request.frame.shape)
        path = save_frame_to_redis(request.string_map['id'], frame, self.redis)
        clear_frame_set_path(request, path)

        json_no_newlines = json_format.MessageToJson(request).replace('\n', '')
        http_event = f"event:detection\ndata:{json_no_newlines}\nid:{request.string_map['id']}\n\n"
        self.redis.publish(self.channel, http_event)
        logging.info(f'placed request on queue, frame_count: {request.frame_count}')
        return detection_handler_pb2.handle_detection_response(status=True)
