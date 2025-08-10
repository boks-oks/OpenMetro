import json
import os
import xml
import requests

# Unlike the others, this one is JSON!

url = "https://www.themealdb.com/api/json/v1/1/random.php"
response = requests.get(url)
data = response.json()

def grab_article():
    img = data["meals"][0]["strMealThumb"]
    return img

# No need for setvars() here, just return the image in it's XML.
# That was easy.
def main():
    with open(os.path.join("tile", "food.xml"), 'r') as f:
        xml_content = f.read()
    xml_content = xml_content.replace("{i1}", grab_article())
    return xml_content