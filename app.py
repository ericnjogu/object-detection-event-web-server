import argparse
import logging

from proto.generated import detection_handler_pb2_grpc, detection_handler_pb2
import web_handler

#if __name__ == '__main__':
# parse args
parser = argparse.ArgumentParser(description=" stream detected object events to web clients")
parser.add_argument("handler_port", help="port to listen for detection handling requests")
parser.add_argument("--testing", help="add some test items to the event queue on startup", action="store_true")
args = parser.parse_args()

web_handler_app = web_handler.WebDetectionHandler(__name__)
logging.info(f"created web handler with id: {id(web_handler_app)}")

# start grpc server
web_handler_app.start_grpc_server(args.handler_port)
# start flask
web_handler_app.debug = True
web_handler_app.run()
