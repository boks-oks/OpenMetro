from mitmproxy import http, ctx
import re
import requests
import random
import json
import xml.etree.ElementTree as ET
from html import escape
import math
import time
import csv
from io import StringIO

# --- Configuration & Constants ---
WEATHER_LATITUDE = "40.713"  # New York City latitude
WEATHER_LONGITUDE = "-74.007"  # New York City longitude
MAX_ARTICLES = 6  # How many articles to fetch for cycling tiles

# RSS Feeds for News and Sports (no API key required)
NEWS_RSS_URL = "http://feeds.bbci.co.uk/news/rss.xml"
SPORTS_RSS_URL = "http://feeds.bbci.co.uk/sport/rss.xml"  # Use BBC Sport
FINANCE_RSS_URL = (
    "https://www.marketwatch.com/rss/topstories"  # Using headlines for finance
)

# Add a default browser-like User-Agent for all RSS requests
DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    )
}

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


def parse_rss_feed(url, num_items=MAX_ARTICLES, extract_image=False):
    """
    Fetches and parses an RSS feed, returning a list of headlines (and optionally images).
    Returns an empty list if fetching or parsing fails.
    """
    try:
        response = requests.get(url, timeout=10, headers=DEFAULT_HEADERS)
        response.raise_for_status()
        root = ET.fromstring(response.content)
        items = []
        for item in root.findall(".//channel/item")[:num_items]:
            title_elem = item.find("title")
            title = (
                title_elem.text
                if title_elem is not None and title_elem.text is not None
                else "No Title"
            )
            image_url = None
            if extract_image:
                # Try to get image from <media:content>, <media:thumbnail>, <enclosure>, <image>, <url>
                media_content = item.find("{http://search.yahoo.com/mrss/}content")
                if media_content is not None and "url" in media_content.attrib:
                    image_url = media_content.attrib["url"]
                if not image_url:
                    media_thumb = item.find("{http://search.yahoo.com/mrss/}thumbnail")
                    if media_thumb is not None and "url" in media_thumb.attrib:
                        image_url = media_thumb.attrib["url"]
                if not image_url:
                    enclosure = item.find("enclosure")
                    if enclosure is not None and "url" in enclosure.attrib:
                        image_url = enclosure.attrib["url"]
                if not image_url:
                    image_tag = item.find("image")
                    if image_tag is not None and image_tag.text:
                        image_url = image_tag.text
                if not image_url:
                    url_tag = item.find("url")
                    if (
                        url_tag is not None
                        and url_tag.text
                        and url_tag.text.startswith("http")
                    ):
                        image_url = url_tag.text
                # Some feeds put images in <description> as <img src="...">
                if not image_url:
                    desc_elem = item.find("description")
                    desc = (
                        desc_elem.text
                        if desc_elem is not None and desc_elem.text
                        else ""
                    )
                    m = re.search(r'<img[^>]+src="([^"]+)"', desc)
                    if m:
                        image_url = m.group(1)
            items.append(
                {"title": title, "image": image_url}
                if extract_image
                else {"title": title}
            )
        return items
    except (requests.RequestException, ET.ParseError) as e:
        ctx.log.error(f"Error parsing RSS feed {url}: {e}")
        return []


def get_geoip_location():
    """Gets the latitude and longitude from GeoIP service (ipinfo.io)."""
    try:
        resp = requests.get("https://ipinfo.io/json", timeout=5)
        resp.raise_for_status()
        data = resp.json()
        loc = data.get("loc", None)
        if loc:
            lat, lon = loc.split(",")
            return lat.strip(), lon.strip()
    except Exception as e:
        ctx.log.error(f"GeoIP lookup failed: {e}")
    return None, None


# Set lat/lon from GeoIP if configured as "auto"
if WEATHER_LATITUDE.lower() == "auto" or WEATHER_LONGITUDE.lower() == "auto":
    lat, lon = get_geoip_location()
    if lat and lon:
        WEATHER_LATITUDE = lat
        WEATHER_LONGITUDE = lon


def generate_weather_tile():
    """
    Fetches weather from the US National Weather Service (NWS) API
    and builds a tile for all sizes.
    Supports both /forecast and /gridpoints/.../forecast endpoints.
    Shows city/state from NWS points API.
    """
    try:
        points_url = (
            f"https://api.weather.gov/points/{WEATHER_LATITUDE},{WEATHER_LONGITUDE}"
        )
        headers = {"User-Agent": "MitmproxyWeatherTile/1.0"}
        points_response = requests.get(points_url, headers=headers, timeout=15)
        points_response.raise_for_status()
        points_data = points_response.json()
        forecast_url = points_data["properties"]["forecast"]

        # Get city/state from relativeLocation
        rel_loc = (
            points_data["properties"].get("relativeLocation", {}).get("properties", {})
        )
        city = rel_loc.get("city", "Unknown City")
        state = rel_loc.get("state", "")
        location_display = f"{city}, {state}".strip(", ")

        forecast_response = requests.get(forecast_url, headers=headers, timeout=15)
        forecast_response.raise_for_status()
        forecast_data = forecast_response.json()

        # Try to get periods from both possible structures
        periods = None
        if "properties" in forecast_data and "periods" in forecast_data["properties"]:
            periods = forecast_data["properties"]["periods"]
        elif "periods" in forecast_data:
            periods = forecast_data["periods"]
        else:
            raise KeyError("No periods found in forecast data")

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
                    <text id="1">{escape(location_display)}</text>
                    <text id="2">{escape(square_text)}</text>
                </binding>
                <binding template="TileWide310x150Text01" fallback="TileWideText01">
                    <text id="1">{escape(wide_text)}</text>
                </binding>
                <binding template="TileSquare310x310TextList02" fallback="TileSquare310x310TextList02">
                    <text id="1">{escape(location_display)} Weather</text>
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
    news_items = parse_rss_feed(
        NEWS_RSS_URL, num_items=MAX_ARTICLES, extract_image=True
    )
    if not news_items:
        headline = "No news available at the moment."
        image_url_150 = image_url_310x150 = image_url_310 = (
            "https://placehold.co/310x310/A83232/FFFFFF/png?text=News"
        )
    else:
        # Cycle through articles based on the index from the URL
        item = news_items[article_index % len(news_items)]
        headline = item["title"]
        image_url = (
            item.get("image")
            or "https://placehold.co/310x310/A83232/FFFFFF/png?text=News"
        )
        # Use the same image for all sizes, or adjust if your source supports it
        image_url_150 = image_url
        image_url_310x150 = image_url
        image_url_310 = image_url

    return f"""
    <tile>
        <visual version="2" lang="en-US">
            <binding template="TileSquare150x150PeekImageAndText04" fallback="TileSquarePeekImageAndText04">
                <image id="1" src="{escape(image_url_150)}" alt=""/>
                <text id="1">{escape(headline)}</text>
            </binding>
            <binding template="TileWide310x150ImageAndText01" fallback="TileWideImageAndText01">
                <image id="1" src="{escape(image_url_310x150)}" alt=""/>
                <text id="1">{escape(headline)}</text>
            </binding>
            <binding template="TileSquare310x310ImageAndText01">
                <image id="1" src="{escape(image_url_310)}" alt=""/>
                <text id="1">{escape(headline)}</text>
            </binding>
        </visual>
    </tile>
    """


# --- Simple in-memory cache for stock data ---
_stock_cache = {}


def fetch_stock_data(symbol):
    """
    Fetches latest stock price and recent history for a symbol using Stooq (no API key).
    Returns (current_price, change, [history_prices]).
    Uses a 5-minute cache to avoid rate limiting.
    """
    now = int(time.time() // 300)
    cache_key = f"{symbol}:{now}"
    if cache_key in _stock_cache:
        return _stock_cache[cache_key]
    try:
        # Stooq: symbol must be like 'aapl.us', 'msft.us', '^spx' is '^spx' on stooq
        stooq_symbol = symbol.lower().replace("^gspc", "^spx") + (
            ".us" if symbol not in ["^GSPC", "^spx"] else ""
        )
        # Latest quote
        quote_url = f"https://stooq.com/q/l/?s={stooq_symbol}&f=sd2t2ohlcv&h&e=csv"
        resp = requests.get(quote_url, timeout=5)
        resp.raise_for_status()
        reader = csv.DictReader(StringIO(resp.text))
        row = next(reader)
        price = float(row["Close"])
        prev_close = float(
            row["Open"]
        )  # Stooq doesn't provide prev close, so use Open as a proxy
        change = price - prev_close

        # Recent history for chart (last 1 day, 5-min intervals)
        hist_url = f"https://stooq.com/q/d/l/?s={stooq_symbol}&i=5"
        resp_hist = requests.get(hist_url, timeout=5)
        resp_hist.raise_for_status()
        reader_hist = csv.DictReader(StringIO(resp_hist.text))
        prices = [
            float(r["Close"])
            for r in reader_hist
            if r.get("Close") not in (None, "", "N/A")
        ]

        _stock_cache[cache_key] = (price, change, prices)
        return price, change, prices
    except Exception as e:
        ctx.log.error(f"Stock fetch error for {symbol} (Stooq): {e}")
        _stock_cache[cache_key] = (None, None, [])
        return None, None, []


def generate_stock_chart_url(prices, symbol):
    """
    Returns a QuickChart.io URL for a simple line chart of the stock prices.
    """
    if not prices:
        return "https://placehold.co/310x150/006400/FFFFFF/png?text=No+Chart"
    chart = {
        "type": "sparkline",
        "data": {
            "datasets": [
                {
                    "data": prices,
                    "borderColor": "green",
                    "fill": False,
                }
            ]
        },
        "options": {
            "scales": {"y": {"display": False}, "x": {"display": False}},
            "elements": {"point": {"radius": 0}},
            "plugins": {"legend": False, "title": {"display": False}},
        },
    }
    import urllib.parse, json as pyjson

    chart_url = "https://quickchart.io/chart"
    params = urllib.parse.urlencode({"c": pyjson.dumps(chart), "w": 310, "h": 150})
    return f"{chart_url}?{params}"


def generate_finance_tile(article_index=0):
    """Generates a finance tile showing stock changes (no images), supports cycling."""
    symbols = ["^GSPC", "AAPL", "MSFT", "GOOG", "AMZN"]
    name_map = {
        "^GSPC": "S&P 500",
        "AAPL": "Apple",
        "MSFT": "Microsoft",
        "GOOG": "Google",
        "AMZN": "Amazon",
    }
    symbol = symbols[article_index % len(symbols)]
    display_name = name_map.get(symbol, symbol)
    price, change, prices = fetch_stock_data(symbol)
    # Ensure all text fields are non-empty
    if price is None:
        headline = "No market data available."
        change_str = ""
        subline = display_name
    else:
        sign = "+" if change >= 0 else ""
        change_str = f"{sign}{change:.2f}"
        headline = f"{display_name}: {price:.2f} ({change_str})"
        subline = f"Symbol: {symbol}"

    # Add a second text line for all tile sizes to avoid "payload too small"
    return f"""
    <tile>
        <visual version="2" lang="en-US">
            <binding template="TileSquare150x150Text02" fallback="TileSquareText02">
                <text id="1">{escape(headline)}</text>
                <text id="2">{escape(subline)}</text>
            </binding>
            <binding template="TileWide310x150Text01" fallback="TileWideText01">
                <text id="1">{escape(headline)}</text>
                <text id="2">{escape(subline)}</text>
            </binding>
            <binding template="TileSquare310x310Text01">
                <text id="1">{escape(headline)}</text>
                <text id="2">{escape(subline)}</text>
            </binding>
        </visual>
    </tile>
    """


def generate_sports_tile(article_index=None):
    """Generates a sports tile from BBC Sport RSS feed using the provided template."""
    sports_items = parse_rss_feed(SPORTS_RSS_URL, num_items=5, extract_image=True)
    headline = "No sports news available."
    image_url_150 = (
        "http://appexdb3.stb.s-msn.com/emeaappex/i/E3/95AE66E09EB624CDCC3237743BDA8.jpg"
    )
    image_url_310x150 = "http://appexdb3.stb.s-msn.com/emeaappex/i/F3/D264824732A9361AC0A4C6AF7C2196.jpg"
    image_url_310 = (
        "http://appexdb3.stb.s-msn.com/emeaappex/i/AA/89B115AE26947D1CE665736A37731.jpg"
    )
    if sports_items:
        if article_index is None:
            # Rotate every 5 minutes
            idx = int(time.time() // 300) % len(sports_items)
            item = sports_items[idx]
        else:
            item = sports_items[article_index % len(sports_items)]
        headline = item["title"] or "Latest sports news"
        img = item.get("image")
        if img:
            image_url_150 = image_url_310x150 = image_url_310 = img

    return f"""<tile>
<visual version="2" lang="en-gb">
<binding template="TileSquare150x150PeekImageAndText04" fallback="TileSquarePeekImageAndText04">
<image id="1" src="{escape(image_url_150)}" alt=""/>
<text id="1">{escape(headline)}</text>
</binding>
<binding template="TileWide310x150ImageAndText01" fallback="TileWideImageAndText01">
<image id="1" src="{escape(image_url_310x150)}" alt=""/>
<text id="1">{escape(headline)}</text>
</binding>
<binding template="TileSquare310x310ImageAndText01">
<image id="1" src="{escape(image_url_310)}" alt=""/>
<text id="1">{escape(headline)}</text>
</binding>
</visual>
</tile>"""


def generate_openmeteo_weather_tile():
    """
    Fetches weather data from OpenMeteo and returns a custom tile XML
    using the provided template and static assets.
    """
    # Washington, DC coordinates
    lat, lon = 38.89511, -77.03637
    city = "Washington, DC"
    # OpenMeteo API: get current and 5-day forecast
    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={lat}&longitude={lon}&current_weather=true"
        f"&daily=temperature_2m_max,temperature_2m_min,weathercode"
        f"&timezone=America/New_York"
    )
    try:
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        current = data["current_weather"]
        daily = data["daily"]
        # Current
        temp = int(round(current["temperature"]))
        condition_code = current["weathercode"]
        # Map OpenMeteo weathercode to icon and description (simplified)
        code_map = {
            0: ("Sunny", "5.jpg", "19.png"),
            1: ("Mainly Clear", "5.jpg", "19.png"),
            2: ("Partly Cloudy", "5.jpg", "19.png"),
            3: ("Cloudy", "5.jpg", "5.png"),
            45: ("Fog", "5.jpg", "5.png"),
            48: ("Depositing Rime Fog", "5.jpg", "5.png"),
            51: ("Drizzle", "5.jpg", "2.png"),
            53: ("Drizzle", "5.jpg", "2.png"),
            55: ("Drizzle", "5.jpg", "2.png"),
            56: ("Freezing Drizzle", "5.jpg", "2.png"),
            57: ("Freezing Drizzle", "5.jpg", "2.png"),
            61: ("Rain", "5.jpg", "2.png"),
            63: ("Rain", "5.jpg", "2.png"),
            65: ("Rain", "5.jpg", "2.png"),
            66: ("Freezing Rain", "5.jpg", "2.png"),
            67: ("Freezing Rain", "5.jpg", "2.png"),
            71: ("Snow", "5.jpg", "19.png"),
            73: ("Snow", "5.jpg", "19.png"),
            75: ("Snow", "5.jpg", "19.png"),
            77: ("Snow Grains", "5.jpg", "19.png"),
            80: ("Showers", "5.jpg", "2.png"),
            81: ("Showers", "5.jpg", "2.png"),
            82: ("Showers", "5.jpg", "2.png"),
            85: ("Snow Showers", "5.jpg", "19.png"),
            86: ("Snow Showers", "5.jpg", "19.png"),
            95: ("Thunderstorm", "5.jpg", "2.png"),
            96: ("Thunderstorm", "5.jpg", "2.png"),
            99: ("Thunderstorm", "5.jpg", "2.png"),
        }
        condition, bg_img, icon_img = code_map.get(
            condition_code, ("Cloudy", "5.jpg", "5.png")
        )
        # Forecast for next 5 days
        days = daily["time"]
        highs = daily["temperature_2m_max"]
        lows = daily["temperature_2m_min"]
        codes = daily["weathercode"]
        # Day names
        import datetime

        today = datetime.datetime.now()
        day_names = [
            (today + datetime.timedelta(days=i)).strftime("%a") for i in range(5)
        ]
        # Compose subgroups for TileLarge
        large_subgroups = ""
        for i in range(5):
            day = day_names[i]
            hi = int(round(highs[i]))
            lo = int(round(lows[i]))
            code = codes[i]
            _, _, icon = code_map.get(code, ("Cloudy", "5.jpg", "5.png"))
            large_subgroups += f"""
<subgroup hint-weight="18">
<text hint-align="center">{day}</text>
<image hint-align="center" src="WeatherIcons/30x30/{icon}"/>
<text hint-align="center">{hi}°</text>
<text hint-style="captionsubtle" hint-align="center">{lo}°</text>
</subgroup>
"""
        # For Medium/Wide: use today's hi/lo
        hi_today = int(round(highs[0]))
        lo_today = int(round(lows[0]))
        # For humidity/wind: OpenMeteo current_weather does not provide, so use placeholders
        humidity = "94%"
        wind = f"{int(round(current.get('windspeed', 9)))} mph"
        # Compose XML
        return f"""<tile>
<visual version="2" Branding="name" baseUri="http://assets.msn.com/weathermapdata/1/static/mws-new/" hint-lockDetailedStatus1="{city} {temp}°" hint-lockDetailedStatus2="" hint-lockDetailedStatus3="">
<binding template="TileSmall" hint-textStacking="center" hint-overlay="30" branding="none">
<image placement="background" src="WeatherImages/210x173/{bg_img}?a"/>
<text hint-style="caption" hint-align="center">{city}</text>
<text hint-style="base" hint-align="center">{temp}°</text>
</binding>
<binding template="TileMedium" DisplayName="{city}" hint-overlay="30">
<image placement="background" src="WeatherImages/210x173/{bg_img}?a"/>
<text>{condition}</text>
<image hint-removeMargin="True" hint-align="center" src="ms-appx:///Assets/AppTiles/Spacer/6px.png"/>
<group>
<subgroup hint-weight="70" hint-textStacking="center">
<image hint-removeMargin="True" hint-align="center" src="ms-appx:///Assets/AppTiles/Spacer/2px.png"/>
<text hint-style="titleNumeral">{temp}°</text>
</subgroup>
<subgroup hint-weight="30">
<image hint-removeMargin="True" hint-align="center" src="ms-appx:///Assets/AppTiles/Spacer/6px.png"/>
<text>{hi_today}°</text>
<text hint-style="captionsubtle">{lo_today}°</text>
</subgroup>
</group>
</binding>
<binding template="TileWide" DisplayName="{city}" hint-overlay="30">
<image placement="background" src="WeatherImages/423x173/{bg_img}?a"/>
<text>{condition}</text>
<image hint-removeMargin="True" hint-align="center" src="ms-appx:///Assets/AppTiles/Spacer/6px.png"/>
<group>
<subgroup hint-weight="32" hint-textStacking="center">
<image hint-removeMargin="True" hint-align="center" src="ms-appx:///Assets/AppTiles/Spacer/2px.png"/>
<text hint-style="titleNumeral">{temp}°</text>
</subgroup>
<subgroup hint-weight="20">
<image hint-removeMargin="True" hint-align="center" src="ms-appx:///Assets/AppTiles/Spacer/6px.png"/>
<text>{hi_today}°</text>
<text hint-style="captionsubtle">{lo_today}°</text>
</subgroup>
<subgroup hint-weight="10">
<image hint-removeMargin="True" hint-align="center" src="ms-appx:///Assets/AppTiles/Spacer/6px.png"/>
<image hint-removeMargin="True" hint-align="center" src="LiveTile/Icons_Icon_PoP_sm.png?a"/>
<image hint-removeMargin="True" hint-align="center" src="ms-appx:///Assets/AppTiles/Spacer/4px.png"/>
<image hint-removeMargin="True" hint-align="center" src="LiveTile/W1.png?a"/>
</subgroup>
<subgroup hint-weight="38">
<image hint-removeMargin="True" hint-align="center" src="ms-appx:///Assets/AppTiles/Spacer/6px.png"/>
<text>{humidity}</text>
<text>{wind}</text>
</subgroup>
</group>
</binding>
<binding template="TileLarge" DisplayName="{city}" hint-overlay="30">
<image placement="background" src="WeatherImages/210x173/{bg_img}?a"/>
<text>{condition}</text>
<image hint-removeMargin="True" hint-align="center" src="ms-appx:///Assets/AppTiles/Spacer/6px.png"/>
<group>
<subgroup hint-weight="100">
<image hint-removeMargin="True" hint-align="center" src="ms-appx:///Assets/AppTiles/Spacer/2px.png"/>
<text hint-style="subheaderNumeral">{temp}°</text>
</subgroup>
</group>
<text/>
<group>
{large_subgroups}
</group>
</binding>
</visual>
</tile>"""
    except Exception as e:
        ctx.log.error(f"OpenMeteo weather error: {e}")
        return """<tile><visual><binding template="TileSquare150x150Text01"><text id="1">Weather Unavailable</text></binding></visual></tile>"""


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

    # Finance App Tile - support for cycling stocks (today.xml, today/1.xml, ...)
    elif re.search(
        r"en-us\.appex-rf\.msn\.com/cgtile/v1/.+/finance/(?:today|today/(\d+))\.xml",
        url,
        re.IGNORECASE,
    ):
        ctx.log.info(f"Intercepted Finance Tile request for URL: {url}")
        article_index = 0
        if re.search(r"/finance/today/(\d+)\.xml", url):
            try:
                article_index = int(
                    re.search(r"/finance/today/(\d+)\.xml", url).group(1)
                )
            except (ValueError, IndexError):
                article_index = 0
        make_response(generate_finance_tile(article_index))
        return

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

    # Sports App Tile - support for cycling articles (today.xml, today/1.xml, today/2.xml, ...)
    elif re.search(
        r"en-us\.appex-rf\.msn\.com/cgtile/v1/.+/sports/(?:today|today/(\d+))\.xml",
        url,
        re.IGNORECASE,
    ):
        ctx.log.info(f"Intercepted Sports Tile request for URL: {url}")
        article_index = 0
        if re.search(r"/sports/today/(\d+)\.xml", url):
            try:
                article_index = int(
                    re.search(r"/sports/today/(\d+)\.xml", url).group(1)
                )
            except (ValueError, IndexError):
                article_index = 0
        make_response(generate_sports_tile(article_index))
        return

    # Weather App Tile
    elif re.search(
        r"weather\.tile\.appex\.bing.com/weatherservice\.svc/livetilev2",
        url,
        re.IGNORECASE,
    ):
        ctx.log.info("Intercepted Weather Tile request.")
        make_response(generate_weather_tile())

    # --- Weather App Tile (Bing Weather style, OpenMeteo backend) ---
    if re.search(
        r"www\.bing\.com/(weather|search)\?.*WeatherOverviewByLatLongV1",
        url,
        re.IGNORECASE,
    ):
        ctx.log.info("Intercepted Bing Weather Tile request (OpenMeteo frontend).")
        make_response(generate_openmeteo_weather_tile())
        return

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
