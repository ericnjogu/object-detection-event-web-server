import numpy
import logging
import imageio
import io

from juu_object_detection_protos.api.generated import detection_handler_pb2

FRAMES_ROUTE = '/frames'
FRAME_KEY = 'frame_path'


def save_frame_to_redis(request, redis):
    """
    save frame to redis  as jpeg using the request id as a key
    :param request: a protobuf detection request
    :param frame: numpy array
    :param redis: redis client
    :return: None
    """
    ndarray = numpy.array(request.frame.numbers, dtype=numpy.uint8).reshape(request.frame.shape)
    bytes_io = io.BytesIO()
    imageio.imwrite(bytes_io, ndarray, format='JPEG-PIL')
    key = f"{FRAMES_ROUTE}/{request.string_map['id']}.jpg"
    redis.set(key, bytes_io.getvalue())
    # TODO set expire on the key - using a configurable value

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
