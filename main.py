import os
from mitmproxy import http
from handlers import finance, food, news, games, travel, weather
import handlers
# from handlers.app import mapcfg, weather, imagemap
import re

def request(flow: http.HTTPFlow) -> None:
    url = flow.request.url.lower()
    if "en-us.appex-rf.msn.com/cgtile/v1/en-us/news" in url:
        match = re.search(r"/(?:(\d+)|today)\.xml$", url.lower())
        if match:
            if 'today' in match.group(0).lower():
                tile_num = 1
            else:
                tile_num = int(match.group(1))
                
            if 1 <= tile_num <= 4:
                flow.response = news.handle_request(flow, tile_num)
    elif "cdf-anon.xboxlive.com/en-us/x8/feeds/1.1/tile-games" in url:
        games.handle_request(flow)
    elif "http://foodanddrink.services.appex.bing.com/api/feed/" in url:
        food.handle_request(flow) 
    elif "http://finance.services.appex.bing.com/market.svc/apptilev2" in url:
        finance.handle_request(flow)
    elif "http://travel.tile.appex.bing.com/api/livetile.xml" in url:
        travel.handle_request(flow)
    elif "weather.tile.appex.bing.com" in url and "livetilev2" in url:
        handlers.weather.handle_request(flow)

    # if "weatheroverviewbylatlong" in url and flow.request.method == "GET":
    #     flow.response = weather.handle_request(flow)
    # elif "imageconfig" in url:
    #     flow.response = imagemap.handle_request()
    # elif "mapcontrol" in url:
    #     flow.response = mapcfg.handle_request()