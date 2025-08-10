from mitmproxy import http
from mitmproxy.http import Response
from logic.food import *

def handle_request(flow):
    xml_content = main()
    flow.response = Response.make(200, xml_content, {"Content-Type": "application/xml"})
    return flow.response