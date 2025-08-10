import feedparser 
import os

url = "https://feeds.feedburner.com/ign/games-all" # IGN games RSS feed.
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
            img = f"https://images.weserv.nl/?url={img}&w=400&h=400" if use_weserv else img
        desc = entry.get("description")
        if img and amnt_imgs != amnt_imgs_max:
            amnt_imgs = amnt_imgs + 1
            imgs.append({"im": img, "de": desc})
    return imgs

def setvars():
    articles = grab_articles()

    # Articles
    a1 = articles[0]

    # Images
    im1 = a1["im"]

    # Descriptions
    de1 = a1["de"]

    return im1, de1

def main():
    im1, de1 = setvars()

    with open(os.path.join("tile", "games.xml"), 'r') as f:
        xml_content = f.read()

        xml_content = xml_content.replace('{i1a1}', im1)
        xml_content = xml_content.replace('{t1a1}', de1)
        # Escape &
        xml_content = xml_content.replace('&', '&amp;')

    return xml_content