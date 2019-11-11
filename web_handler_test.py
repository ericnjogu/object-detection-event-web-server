from web_handler import frame_array_to_image_data
from proto.generated import detection_handler_pb2


def test_frame_array_to_image_data():
    frame = detection_handler_pb2.float_array(numbers=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12], shape=[1, 4, 3])
    img_data = frame_array_to_image_data(frame)
    assert img_data == [1, 2, 3, 255, 4, 5, 6, 255, 7, 8, 9, 255, 10, 11, 12, 255]