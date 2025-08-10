import feedparser 
import os

url = "https://rss.nytimes.com/services/xml/rss/nyt/World.xml" # NYT world RSS feed.
feed = feedparser.parse(url) # Parse the URL. It returns raw data of that RSS feed.
use_weserv = True # Downscale images to 400x400 using Weserv?

def grab_articles():
    imgs = []
    amnt_imgs = 0 # Reset counter
    amnt_imgs_max = 4
    for entry in feed["entries"]:
        img = None
        if "media_content" in entry and entry["media_content"]:
            img = entry["media_content"][0].get("url")
            img = f"https://images.weserv.nl/?url={img}&amp;w=400&amp;h=400" if use_weserv else img
        desc = entry.get("description")
        if img and amnt_imgs != amnt_imgs_max:
            amnt_imgs = amnt_imgs + 1
            imgs.append({"im": img, "de": desc})
    return imgs

"""
a1: Tile "today.xml"
a2: Tile "2.xml"
a3: Tile "3.xml"
a4: Tile "4.xml"

The articles are mapped to tiles by replacing the placeholders in the XML file with the actual data. I know it looks a bit messy, but it works. ;)
"""

def setvars():
    articles = grab_articles()

    # Articles
    a1 = articles[0]
    a2 = articles[1]
    a3 = articles[2]
    a4 = articles[3]

    # Images
    im1 = a1["im"]
    im2 = a2["im"]
    im3 = a3["im"]
    im4 = a4["im"]

    # Descriptions
    de1 = a1["de"]
    de2 = a2["de"]
    de3 = a3["de"]
    de4 = a4["de"]

    replacements = {
        '{i1a1}': im1,
        '{t1a1}': de1,
        '{i1a2}': im2,
        '{t1a2}': de2,
        '{i1a3}': im3,
        '{t1a3}': de3,
        '{i1a4}': im4,
        '{t1a4}': de4  
    }

    return im1, im2, im3, im4, de1, de2, de3, de4, replacements

def main(tileindex):
    im1, im2, im3, im4, de1, de2, de3, de4, replacements = setvars()

    if tileindex == 1:
        tile_file = "today.xml"
    elif tileindex == 2:
        tile_file = "2.xml"
    elif tileindex == 3:
        tile_file = "3.xml"
    elif tileindex == 4:
        tile_file = "4.xml"
    # Listen, not everything has to be all neat and tidy. "If it works, don't fix it!". Hehe, I enjoy writing these little comments.

    with open(os.path.join("tile", "news", tile_file), 'r') as f:
        xml_content = f.read()

    for placeholder, replacement_value in replacements.items():
        xml_content = xml_content.replace(placeholder, replacement_value)

    return xml_content