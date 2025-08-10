from mitmproxy import http
from mitmproxy.http import Response
from logic.news import *

def handle_request(flow, num_tile):
    xml_content = main(num_tile)
    flow.response = Response.make(200, xml_content, {"Content-Type": "application/xml"})
    return flow.response