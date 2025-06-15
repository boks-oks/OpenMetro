from mitmproxy import http, ctx
import re
import requests
import random
import json
import xml.etree.ElementTree as ET
from html import escape
import math

# --- Configuration & Constants ---
WEATHER_LATITUDE = "00.00"  # You aren't getting my [LATITUDE] today!
WEATHER_LONGITUDE = "00.00"  # You aren't getting my [LONGITUDE] today!
MAX_ARTICLES = 6  # How many articles to fetch for cycling tiles

# RSS Feeds for News and Sports (no API key required)
NEWS_RSS_URL = "http://feeds.bbci.co.uk/news/rss.xml"
SPORTS_RSS_URL = "https://www.espn.com/espn/rss/news"
FINANCE_RSS_URL = (
    "https://www.marketwatch.com/rss/topstories"  # Using headlines for finance
)

# --- Helper Functions for Tile Generation ---


def get_random_health_tip():
    """Returns a random health and fitness tip."""
    tips = [
        "Drink at least 8 glasses of water a day to stay hydrated.",
        "Take a brisk 10-minute walk after each meal to aid digestion.",
        "Aim for 7-9 hours of quality sleep per night for optimal health.",
        "Incorporate more fruits and vegetables into your daily diet.",
        "Practice mindfulness or meditation for 5 minutes to reduce stress.",
        "Stretch your body every morning to improve flexibility and energy.",
        "Choose whole grains over refined grains for better nutrition.",
        "Limit sugary drinks and snacks to maintain stable energy levels.",
    ]
    return random.choice(tips)


def parse_rss_feed(url, num_items=MAX_ARTICLES):
    """
    Fetches and parses an RSS feed, returning a list of headlines.
    Returns an empty list if fetching or parsing fails.
    """
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        root = ET.fromstring(response.content)
        items = []
        for item in root.findall(".//channel/item")[:num_items]:
            title = (
                item.find("title").text
                if item.find("title") is not None
                else "No Title"
            )
            items.append({"title": title})
        return items
    except (requests.RequestException, ET.ParseError) as e:
        ctx.log.error(f"Error parsing RSS feed {url}: {e}")
        return []


def generate_weather_tile():
    """
    Fetches weather from the US National Weather Service (NWS) API
    and builds a tile for all sizes.
    """
    try:
        points_url = (
            f"https://api.weather.gov/points/{WEATHER_LATITUDE},{WEATHER_LONGITUDE}"
        )
        headers = {"User-Agent": "MitmproxyWeatherTile/1.0"}
        points_response = requests.get(points_url, headers=headers, timeout=5)
        points_response.raise_for_status()
        forecast_url = points_response.json()["properties"]["forecast"]

        forecast_response = requests.get(forecast_url, headers=headers, timeout=5)
        forecast_response.raise_for_status()
        forecast_data = forecast_response.json()

        periods = forecast_data["properties"]["periods"]
        city = forecast_data["properties"]["timeZone"].split("/")[-1].replace("_", " ")

        # Content for different tile sizes
        current = periods[0]
        temp = current["temperature"]
        unit = current["temperatureUnit"]
        short_forecast = current["shortForecast"]

        square_text = f"{temp}°{unit} {short_forecast}"
        wide_text = (
            f"Forecast: {current['name']}, {short_forecast}, high of {temp}°{unit}."
        )

        # Detailed forecast for the large tile
        large_text_1 = f"{periods[0]['name']}: {periods[0]['detailedForecast']}"
        large_text_2 = (
            f"{periods[1]['name']}: {periods[1]['detailedForecast']}"
            if len(periods) > 1
            else ""
        )

        return f"""
        <tile>
            <visual version="2" lang="en-US">
                <binding template="TileSquare150x150Text02" fallback="TileSquareText02">
                    <text id="1">{escape(city)}</text>
                    <text id="2">{escape(square_text)}</text>
                </binding>
                <binding template="TileWide310x150Text01" fallback="TileWideText01">
                    <text id="1">{escape(wide_text)}</text>
                </binding>
                <binding template="TileSquare310x310TextList02" fallback="TileSquare310x310TextList02">
                    <text id="1">{escape(city)} Weather</text>
                    <text id="2">{escape(large_text_1)}</text>
                    <text id="3">{escape(large_text_2)}</text>
                </binding>
            </visual>
        </tile>
        """
    except (requests.RequestException, KeyError, json.JSONDecodeError) as e:
        ctx.log.error(f"Error fetching weather data: {e}")
        return """
        <tile><visual><binding template="TileSquare150x150Text01"><text id="1">Weather Unavailable</text></binding></visual></tile>
        """


def generate_news_tile(article_index=0):
    """Generates a news tile from a live RSS feed for all tile sizes."""
    news_items = parse_rss_feed(NEWS_RSS_URL, num_items=MAX_ARTICLES)
    if not news_items:
        headline = "No news available at the moment."
    else:
        # Cycle through articles based on the index from the URL
        headline = news_items[article_index % len(news_items)]["title"]

    return f"""
    <tile>
        <visual version="2" lang="en-US">
            <binding template="TileSquare150x150PeekImageAndText04" fallback="TileSquarePeekImageAndText04">
                <image id="1" src="https://placehold.co/150x150/A83232/FFFFFF/png?text=News" alt="News"/>
                <text id="1">{escape(headline)}</text>
            </binding>
            <binding template="TileWide310x150ImageAndText01" fallback="TileWideImageAndText01">
                <image id="1" src="https://placehold.co/310x150/A83232/FFFFFF/png?text=Live%20News" alt="News"/>
                <text id="1">{escape(headline)}</text>
            </binding>
            <binding template="TileSquare310x310ImageAndTextOverlay02" fallback="TileSquare310x310ImageAndTextOverlay02">
                <image id="1" src="https://placehold.co/310x310/A83232/FFFFFF/png?text=Live%20News" alt="Large News"/>
                <text id="1">{escape(headline)}</text>
                <text id="2">From BBC News</text>
            </binding>
        </visual>
    </tile>
    """


def generate_finance_tile():
    """Generates a finance tile using financial news headlines for all tile sizes."""
    finance_items = parse_rss_feed(FINANCE_RSS_URL, num_items=1)
    headline = "No market news available."
    if finance_items:
        headline = finance_items[0]["title"]

    return f"""
    <tile>
        <visual version="2" lang="en-US">
            <binding template="TileSquare150x150Text02" fallback="TileSquareText02">
                <text id="1">Market News</text>
                <text id="2">{escape(headline)}</text>
            </binding>
            <binding template="TileWide310x150Text01" fallback="TileWideText01">
                <text id="1">{escape(headline)}</text>
            </binding>
            <binding template="TileSquare310x310ImageAndTextOverlay02" fallback="TileSquare310x310ImageAndTextOverlay02">
                <image id="1" src="https://placehold.co/310x310/006400/FFFFFF/png?text=Finance" alt="Finance"/>
                <text id="1">MarketWatch Top Story</text>
                <text id="2">{escape(headline)}</text>
            </binding>
        </visual>
    </tile>
    """


def generate_sports_tile():
    """Generates a sports tile from a live RSS feed for all tile sizes."""
    sports_items = parse_rss_feed(SPORTS_RSS_URL, num_items=1)
    headline = "No sports news available."
    if sports_items:
        headline = sports_items[0]["title"]

    return f"""
    <tile>
        <visual version="2" lang="en-US">
            <binding template="TileSquare150x150Text02" fallback="TileSquareText02">
                <text id="1">ESPN Sports</text>
                <text id="2">{escape(headline)}</text>
            </binding>
            <binding template="TileWide310x150Text01" fallback="TileWideText01">
                <text id="1">{escape(headline)}</text>
            </binding>
            <binding template="TileSquare310x310ImageAndTextOverlay03" fallback="TileSquare310x310ImageAndTextOverlay03">
                <image id="1" src="https://placehold.co/310x310/1A4D99/FFFFFF/png?text=Sports" alt="Sports"/>
                <text id="1">ESPN Top Headline</text>
                <text id="2">{escape(headline)}</text>
            </binding>
        </visual>
    </tile>
    """


def request(flow: http.HTTPFlow) -> None:
    """The main entry point for mitmproxy, called for every request."""
    url = flow.request.pretty_url

    def make_response(content, content_type="application/xml; charset=utf-8"):
        flow.response = http.Response.make(
            200, content.encode("utf-8"), {"Content-Type": content_type}
        )

    # --- Live Tile XML Interception ---

    # News App Tile - with support for cycling tiles
    news_match = re.search(
        r"en-us\.appex-rf\.msn\.com/cgtile/v1/.+/news/(?:today|home|today/(\d+))\.xml",
        url,
        re.IGNORECASE,
    )
    if news_match:
        ctx.log.info(f"Intercepted News Tile request for URL: {url}")
        article_index = 0
        if news_match.group(1):
            try:
                article_index = int(news_match.group(1))
            except (ValueError, IndexError):
                article_index = 0  # Default if group is not a valid number

        news_xml = generate_news_tile(article_index)
        make_response(news_xml)

    # Finance App Tile
    elif re.search(
        r"en-us\.appex-rf\.msn\.com/cgtile/v1/.+/finance/.*\.(xml|xaml)",
        url,
        re.IGNORECASE,
    ):
        ctx.log.info("Intercepted Finance Tile request.")
        make_response(generate_finance_tile())

    # Health & Fitness App Tile
    elif re.search(
        r"en-us\.appex-rf\.msn\.com/cgtile/v1/.+/healthandfitness/.*\.(xml|xaml)",
        url,
        re.IGNORECASE,
    ):
        ctx.log.info("Intercepted Health & Fitness Tile request.")
        tip = get_random_health_tip()
        # Modified the square tile template to TileSquare150x150Text05 for better display of single line text
        health_xml = f"""
        <tile>
            <visual version="2" lang="en-US">
                <binding template="TileSquare150x150Text05" fallback="TileSquareText05">
                    <text id="1">{escape(tip)}</text>
                </binding>
                <binding template="TileWide310x150Text01" fallback="TileWideText01">
                    <text id="1">{escape(tip)}</text>
                </binding>
                <binding template="TileSquare310x310Text09" fallback="TileSquare310x310Text09">
                    <text id="1">Health & Fitness Tip</text>
                    <text id="2">{escape(tip)}</text>
                </binding>
            </visual>
        </tile>
        """
        make_response(health_xml)

    # Sports App Tile
    elif re.search(
        r"en-us\.appex-rf\.msn\.com/cgtile/v1/.+/sports/.*\.(xml|xaml)",
        url,
        re.IGNORECASE,
    ):
        ctx.log.info("Intercepted Sports Tile request.")
        make_response(generate_sports_tile())

    # Weather App Tile
    elif re.search(
        r"weather\.tile\.appex\.bing.com/weatherservice\.svc/livetilev2",
        url,
        re.IGNORECASE,
    ):
        ctx.log.info("Intercepted Weather Tile request.")
        make_response(generate_weather_tile())

    # --- Other Critical Interceptions (to prevent app/tile errors) ---

    elif (
        "go.microsoft.com/fwlink" in url
        or "appexnewsappupdate.blob.core.windows.net" in url
        or "newsdaily.services.appex.bing.com" in url
        or "az301819.vo.msecnd.net" in url
        or "finance.services.appex.bing.com" in url
    ):
        flow.response = http.Response.make(
            200, b"{}", {"Content-Type": "application/json"}
        )

    elif "en-us.appex-rf.msn.com/cg/v5/en-us/news/" in url:
        js_content = "// Mitmproxy: In-app content blocked to focus on Live Tile."
        make_response(js_content, "application/javascript; charset=utf-8")
