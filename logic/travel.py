import os
import requests

api = "https://commons.wikimedia.org/w/api.php"

def list_landscapes():
    params = {
        "action": "query",
        "list": "categorymembers",
        "cmtitle": "Category:Landscapes",
        "cmtype": "file",
        "cmlimit": 1,
        "format": "json"
    }
    req = requests.get(api, params=params).json()

    return [m["title"] for m in req["query"]["categorymembers"]]

def get_image(titles):
    params = {
        "action": "query",
        "titles": "|".join(titles),
        "prop": "imageinfo",
        "iiprop": "url",
        "format": "json"
    }
    req = requests.get(api, params=params).json()
    return req["query"]["pages"].popitem()[1]["imageinfo"][0]["url"]

def main():
    img = get_image(list_landscapes())

    url_weserv = f"https://images.weserv.nl/?url={img}&w=400&h=300&fit=cover"

    with open(os.path.join("tile", "travel.xml"), "r") as f:
        xml_content = f.read()

    xml_content = xml_content.replace("{i1}", url_weserv)
    
    xml_content = xml_content.replace("&", "&amp;") # You know the drill...

    return xml_content
    