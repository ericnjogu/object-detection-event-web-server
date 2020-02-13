import numpy
import pytest
import imageio
import tempfile
import logging
import os
from unittest import mock

from web_handler import save_frame_to_redis, FRAMES_ROUTE, clear_frame_set_path
from juu_object_detection_protos.api.generated import detection_handler_pb2


@pytest.fixture
def create_req_msg_from_file_01():
    msg = detection_handler_pb2.handle_detection_request()
    with open('./samples/detection-request-with-frame-01.bin', 'rb') as f:
        msg.ParseFromString(f.read())
    return msg


def test_write_image_file(create_req_msg_from_file_01):
    frame = numpy.array(create_req_msg_from_file_01.frame.numbers, numpy.int32).reshape((400,400,3))
    with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as file:
        imageio.imwrite(file.name, frame)
        logging.debug(f"saved file {file.name}")
        thirty_kb = 30 * 1024
        assert os.stat(file.name).st_size < thirty_kb


def test_save_frame_to_redis():
    ndarray = mock.Mock(reshape=lambda x: 'ndarray')
    id = "1305"
    redis = mock.Mock()
    request = mock.Mock()
    request.string_map = {'id':id}
    expected_path = f"{FRAMES_ROUTE}/{id}.jpg"
    with mock.patch('web_handler.imageio') as mock_imageio:
        with mock.patch('web_handler.io') as io:
            with mock.patch('numpy.array'):
                lunch = "lunch"
                io.BytesIO().getvalue.return_value = lunch
                numpy.array.return_value = ndarray
                path = save_frame_to_redis(request, redis)
                mock_imageio.imwrite.assert_called_with(io.BytesIO(), 'ndarray', format="JPEG-PIL")
                redis.set.assert_called_with(expected_path, lunch)
                assert expected_path == path


def test_clear_frame_set_path():
    request = detection_handler_pb2.handle_detection_request(
        frame=detection_handler_pb2.float_array(numbers=[1,2,3]),
        string_map={"a-key": "1658"})
    path = "/frames/1453.jpg"
    clear_frame_set_path(request, path)
    assert request.frame.numbers == []
    request.string_map['frame_path'] == path
