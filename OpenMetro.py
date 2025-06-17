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
MAX_ARTICLES = 4  # How many articles to fetch for cycling tiles

# RSS Feeds for News and Sports (no API key required)
NEWS_RSS_URL = "http://feeds.bbci.co.uk/news/rss.xml"
SPORTS_RSS_URL = "http://feeds.bbci.co.uk/sport/rss.xml"  # Use BBC Sport
FINANCE_RSS_URL = (
    "https://www.marketwatch.com/rss/topstories"  # Using headlines for finance
)
FOOD_RSS_URL = (
    "https://feeds.feedburner.com/seriouseats/recipes"  # Epicurious food feed
)

# Add a default browser-like User-Agent for all RSS requests
DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    )
}

# Disable images and uses placeholders if set to False. Disabling images
# can improve performance and reduce data usage, especially on mobile networks.
ENABLE_IMAGES = True  # Set to False to disable images and use placeholders
# Enable GeoIP lookup for weather location detection
ENABLE_GEOIP = True  # Set to False to disable GeoIP lookup for weather

print("OpenMetro is ready to go!")

PLACEHOLDER_IMAGE = (
    "https://placehold.co/310x310/cccccc/222222/png?text=Images+\nDisabled"
)

REFRESH_INTERVAL = 300  # 5 minutes in seconds
_last_cache_cleanup = 0
_stock_cache = {}  # Simple in-memory cache for stock data

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


def get_best_location():
    """
    Returns (lat, lon, city, state) using a multi-provider GeoIP approach for improved accuracy.

    1. Try ipinfo.io.
    2. If that fails, try ipapi.co.
    3. If both fail, fallback to configured values.
    Then, use the NWS Points API to retrieve the city and state.
    """
    lat, lon = None, None

    # Try ipinfo.io first
    try:
        resp = requests.get("https://ipinfo.io/json", timeout=5)
        resp.raise_for_status()
        data = resp.json()
        loc = data.get("loc")
        if loc:
            lat, lon = loc.split(",")
    except Exception as e:
        ctx.log.error(f"ipinfo.io lookup failed: {e}")

    # If ipinfo.io failed, try ipapi.co
    if not lat or not lon:
        try:
            resp = requests.get("https://ipapi.co/json", timeout=5)
            resp.raise_for_status()
            data = resp.json()
            lat = str(data.get("latitude"))
            lon = str(data.get("longitude"))
        except Exception as e:
            ctx.log.error(f"ipapi.co lookup failed: {e}")

    # Use config values if GeoIP methods fail
    if not lat or not lon or lat == "None" or lon == "None":
        lat = WEATHER_LATITUDE
        lon = WEATHER_LONGITUDE

    # Retrieve city/state from NWS Points API
    try:
        points_url = f"https://api.weather.gov/points/{lat},{lon}"
        headers = {"User-Agent": "MitmproxyWeatherTile/1.0"}
        points_response = requests.get(points_url, headers=headers, timeout=10)
        points_response.raise_for_status()
        points_data = points_response.json()
        rel_loc = (
            points_data["properties"].get("relativeLocation", {}).get("properties", {})
        )
        city = rel_loc.get("city", "New York")
        state = rel_loc.get("state", "NY")
    except Exception as e:
        ctx.log.error(f"NWS location lookup failed: {e}")
        city = "New York"
        state = "NY"
    return lat, lon, city, state


# Set lat/lon from GeoIP if configured as "auto"
if WEATHER_LATITUDE.lower() == "auto" or WEATHER_LONGITUDE.lower() == "auto":
    location_data = get_best_location()
    if location_data:
        lat, lon, _, _ = location_data
        if lat and lon:
            WEATHER_LATITUDE = lat
            WEATHER_LONGITUDE = lon


def generate_weather_tile():
    """
    Fetches weather from the US National Weather Service (NWS) API
    and builds a tile for all sizes.
    Shows general weather: current temp and tonight's low.
    """
    try:
        lat, lon, city, state = get_best_location()
        location_display = f"{city}, {state}".strip(", ")
        points_url = f"https://api.weather.gov/points/{lat},{lon}"
        headers = {"User-Agent": "MitmproxyWeatherTile/1.0"}
        points_response = requests.get(points_url, headers=headers, timeout=15)
        points_response.raise_for_status()
        points_data = points_response.json()
        forecast_url = points_data["properties"]["forecast"]

        forecast_response = requests.get(forecast_url, headers=headers, timeout=15)
        forecast_response.raise_for_status()
        forecast_data = forecast_response.json()

        # Get periods
        periods = None
        if "properties" in forecast_data and "periods" in forecast_data["properties"]:
            periods = forecast_data["properties"]["periods"]
        elif "periods" in forecast_data:
            periods = forecast_data["periods"]
        else:
            raise KeyError("No periods found in forecast data")

        current = periods[0]
        temp = current["temperature"]
        unit = current["temperatureUnit"]
        short_forecast = current["shortForecast"]

        # Find "Tonight" or next period for low temp
        tonight = None
        for p in periods[1:]:
            if "night" in p["name"].lower() or "tonight" in p["name"].lower():
                tonight = p
                break
        if not tonight and len(periods) > 1:
            tonight = periods[1]

        tonight_temp = tonight["temperature"] if tonight else ""
        tonight_unit = tonight["temperatureUnit"] if tonight else unit
        tonight_label = tonight["name"] if tonight else "Tonight"

        # General weather summary
        square_text = f"{temp}°{unit} {short_forecast}"
        wide_text = f"{location_display}: {temp}°{unit} now, {tonight_label} {tonight_temp}°{tonight_unit}"
        large_text_1 = f"Now: {temp}°{unit}, {short_forecast}"
        large_text_2 = (
            f"{tonight_label}: {tonight_temp}°{tonight_unit}" if tonight else ""
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
        image_url_150 = image_url_310x150 = image_url_310 = PLACEHOLDER_IMAGE
    else:
        # Cycle through articles based on the index from the URL
        item = news_items[article_index % len(news_items)]
        headline = item["title"]
        image_url = (
            item.get("image")
            if ENABLE_IMAGES and item.get("image")
            else PLACEHOLDER_IMAGE
        )
        # Use the same image for all sizes, or adjust if your source supports it
        image_url_150 = image_url_310x150 = image_url_310 = image_url

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


def fetch_stock_data(symbol):
    """
    Fetches latest stock price and recent history for a symbol using Stooq (no API key).
    Returns (current_price, change, [history_prices]).
    Uses a 5-minute cache to avoid rate limiting.
    """
    now = get_refresh_key()  # Use refresh key instead of direct time
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
        sign = "+" if change is not None and change >= 0 else ""
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
    if ENABLE_IMAGES:
        image_url_150 = "http://appexdb3.stb.s-msn.com/emeaappex/i/E3/95AE66E09EB624CDCC3237743BDA8.jpg"
        image_url_310x150 = "http://appexdb3.stb.s-msn.com/emeaappex/i/F3/D264824732A9361AC0A4C6AF7C2196.jpg"
        image_url_310 = "http://appexdb3.stb.s-msn.com/emeaappex/i/AA/89B115AE26947D1CE665736A37731.jpg"
    else:
        image_url_150 = image_url_310x150 = image_url_310 = PLACEHOLDER_IMAGE
    if sports_items:
        if article_index is None:
            idx = int(time.time() // 300) % len(sports_items)
            item = sports_items[idx]
        else:
            item = sports_items[article_index % len(sports_items)]
        headline = item["title"] or "Latest sports news"
        img = item.get("image")
        if ENABLE_IMAGES and img:
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
    # Use GeoIP for user location instead of hardcoded lat/lon
    lat, lon, city, state = get_best_location()
    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={lat}&longitude={lon}&current_weather=true"
        f"&daily=temperature_2m_max,temperature_2m_min,weathercode"
        f"&timezone=America/New_York"
    )
    # Map OpenMeteo weathercode to MSN image codes (fallback to 5)
    # You can expand this mapping as needed for more accuracy
    code_map = {
        0: 5,  # Clear sky
        1: 19,  # Mainly clear
        2: 19,  # Partly cloudy
        3: 5,  # Overcast/Cloudy
        45: 5,  # Fog
        48: 5,  # Depositing rime fog
        51: 2,  # Drizzle
        53: 2,
        55: 2,
        56: 2,  # Freezing Drizzle
        57: 2,
        61: 2,  # Rain
        63: 2,
        65: 2,
        66: 2,  # Freezing Rain
        67: 2,
        71: 19,  # Snow
        73: 19,
        75: 19,
        77: 19,  # Snow grains
        80: 2,  # Showers
        81: 2,
        82: 2,
        85: 19,  # Snow showers
        86: 19,
        95: 2,  # Thunderstorm
        96: 2,
        99: 2,
    }
    # Human-readable descriptions
    desc_map = {
        0: "Clear",
        1: "Mainly Clear",
        2: "Partly Cloudy",
        3: "Cloudy",
        45: "Fog",
        48: "Fog",
        51: "Drizzle",
        53: "Drizzle",
        55: "Drizzle",
        56: "Freezing Drizzle",
        57: "Freezing Drizzle",
        61: "Rain",
        63: "Rain",
        65: "Rain",
        66: "Freezing Rain",
        67: "Freezing Rain",
        71: "Snow",
        73: "Snow",
        75: "Snow",
        77: "Snow Grains",
        80: "Showers",
        81: "Showers",
        82: "Showers",
        85: "Snow Showers",
        86: "Snow Showers",
        95: "Thunderstorm",
        96: "Thunderstorm",
        99: "Thunderstorm",
    }
    try:
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        current = data["current_weather"]
        daily = data["daily"]
        temp = int(round(current["temperature"]))
        condition_code = int(current["weathercode"])
        msn_code = code_map.get(condition_code, 5)
        condition = desc_map.get(condition_code, "Cloudy")
        # 5-day forecast
        highs = daily["temperature_2m_max"]
        lows = daily["temperature_2m_min"]
        codes = daily["weathercode"]
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
            code = int(codes[i])
            msn_icon = code_map.get(code, 5)
            large_subgroups += f"""
<subgroup hint-weight="18">
<text hint-align="center">{day}</text>
<image hint-align="center" src="WeatherIcons/30x30/{msn_icon}.png?a"/>
<text hint-align="center">{hi}°</text>
<text hint-style="captionsubtle" hint-align="center">{lo}°</text>
</subgroup>
"""
        hi_today = int(round(highs[0]))
        lo_today = int(round(lows[0]))
        # Placeholders for additional data (OpenMeteo does not provide humidity/wind in daily)
        humidity = "95%"
        wind = f"{int(round(current.get('windspeed', 4)))} mph"
        # Compose XML using the requested template
        return f"""<tile>
<visual version="2" Branding="name" baseUri="http://assets.msn.com/weathermapdata/1/static/mws-new/" hint-lockDetailedStatus1="{city} {temp}°" hint-lockDetailedStatus2="" hint-lockDetailedStatus3="">
<binding template="TileSmall" hint-textStacking="center" hint-overlay="30" branding="none">
<image placement="background" src="WeatherImages/210x173/{msn_code}.jpg?a"/>
<text hint-style="caption" hint-align="center">{city}</text>
<text hint-style="base" hint-align="center">{temp}°</text>
</binding>
<binding template="TileMedium" DisplayName="{city}" hint-overlay="30">
<image placement="background" src="WeatherImages/210x173/{msn_code}.jpg?a"/>
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
<image placement="background" src="WeatherImages/423x173/{msn_code}.jpg?a"/>
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
<image placement="background" src="WeatherImages/210x173/{msn_code}.jpg?a"/>
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


def get_refresh_key():
    """Returns a key that changes every REFRESH_INTERVAL seconds."""
    return int(time.time() // REFRESH_INTERVAL)


def cleanup_caches():
    """Cleans up old cache entries periodically to prevent memory leaks."""
    global _last_cache_cleanup, _stock_cache
    now = time.time()
    # Only clean up once per REFRESH_INTERVAL
    if now - _last_cache_cleanup > REFRESH_INTERVAL:
        current_period = get_refresh_key()
        # Clean up stock cache
        old_keys = [
            k for k in _stock_cache.keys() if int(k.split(":")[1]) < current_period
        ]
        for k in old_keys:
            del _stock_cache[k]
        _last_cache_cleanup = now


def generate_food_tile(article_index=0):
    """
    Generates a Food & Drink tile using TheMealDB JSON API (not RSS).
    """
    try:
        resp = requests.get(
            "https://www.themealdb.com/api/json/v1/1/random.php", timeout=10
        )
        resp.raise_for_status()
        data = resp.json()
        meal = data.get("meals", [{}])[0]
        title = meal.get("strMeal", "No Title")
        image_url = meal.get("strMealThumb", PLACEHOLDER_IMAGE)
        # Use the same image for all tile sizes
        return f"""<tile>
<visual version="2">
<binding template="TileSquare150x150PeekImageAndText04" fallback="TileSquare150x150Text04">
<image id="1" src="{escape(image_url)}" alt="{escape(title)}" />
<text id="1">{escape(title)}</text>
</binding>
<binding template="TileWide310x150PeekImage03">
<image id="1" src="{escape(image_url)}" alt="{escape(title)}" />
<text id="1">{escape(title)}</text>
</binding>
<binding template="TileSquare310x310ImageAndTextOverlay01">
<image id="1" src="{escape(image_url)}" alt="{escape(title)}" />
<text id="1">{escape(title)}</text>
</binding>
</visual>
</tile>"""
    except Exception as e:
        ctx.log.error(f"Error fetching Food & Drink API: {e}")
        return f"""<tile>
<visual version="2">
<binding template="TileSquare150x150PeekImageAndText04" fallback="TileSquare150x150Text04">
<image id="1" src="{escape(PLACEHOLDER_IMAGE)}" alt="Unavailable" />
<text id="1">Food &amp; Drink Unavailable</text>
</binding>
<binding template="TileWide310x150PeekImage03">
<image id="1" src="{escape(PLACEHOLDER_IMAGE)}" alt="Unavailable" />
<text id="1">Food &amp; Drink Unavailable</text>
</binding>
<binding template="TileSquare310x310ImageAndTextOverlay01">
<image id="1" src="{escape(PLACEHOLDER_IMAGE)}" alt="Unavailable" />
<text id="1">Food &amp; Drink Unavailable</text>
</binding>
</visual>
</tile>"""


def request(flow: http.HTTPFlow) -> None:
    """The main entry point for mitmproxy, called for every request."""
    url = flow.request.pretty_url
    ctx.log.info(f"Request URL: {url}")  # Log the URL for debugging

    def make_response(content, content_type="application/xml; charset=utf-8"):
        """Helper function to create HTTP responses with proper encoding"""
        flow.response = http.Response.make(
            200, content.encode("utf-8"), {"Content-Type": content_type}
        )

    # Define refresh key
    refresh = get_refresh_key()

    # Log all requests to confirm interception
    ctx.log.info(f"Intercepting request: {url}")

    # Food & Drink App Tile
    if re.search(
        r"http?://foodanddrink\.services\.appex\.bing\.com/api/feed/\?view-name=data&name=livetile&market=en-us&version=2_0&format=xml",
        url,
        re.IGNORECASE,
    ):
        ctx.log.info(f"Intercepted Food & Drink Tile request for URL: {url}")
        article_index = refresh % MAX_ARTICLES
        food_xml = generate_food_tile(article_index)
        make_response(food_xml)
        return

    # --- Live Tile XML Interception ---

    # News App Tile - with support for cycling tiles
    news_match = re.search(
        r"en-us\.appex-rf\.msn\.com/cgtile/v1/.+/news/(?:today|home|today/(\d+))\.xml",
        url,
        re.IGNORECASE,
    )
    if news_match:
        ctx.log.info(f"Intercepted News Tile request for URL: {url}")
        article_index = refresh % MAX_ARTICLES  # Cycle through articles based on time
        if news_match.group(1):
            try:
                article_index = int(news_match.group(1))
            except (ValueError, IndexError):
                pass
        news_xml = generate_news_tile(article_index)
        make_response(news_xml)
        return

    # Finance App Tile
    elif re.search(
        r"en-us\.appex-rf\.msn\.com/cgtile/v1/.+/finance/(?:today|today/(\d+))\.xml",
        url,
        re.IGNORECASE,
    ):
        ctx.log.info(f"Intercepted Finance Tile request for URL: {url}")
        article_index = refresh % 5  # Cycle through 5 stocks
        match = re.search(r"/finance/today/(\d+)\.xml", url)
        if match:
            try:
                article_index = int(match.group(1))
            except (ValueError, IndexError):
                pass
        make_response(generate_finance_tile(article_index))
        return

    # Health & Fitness App Tile
    elif re.search(
        r"en-us\.appex-rf\.msn\.com/cgtile/v1/.+/healthandfitness/.*\.(xml|xaml)",
        url,
        re.IGNORECASE,
    ):
        ctx.log.info("Intercepted Health & Fitness Tile request.")
        tip = get_random_health_tip()  # Already random, no need for refresh
        # Use the requested templates and structure
        health_xml = f"""<?xml version="1.0" encoding="utf-8"?>
<tile>
    <visual version="2" lang="en-US">
        <binding template="TileSquare150x150Text04" fallback="TileSquareText04">
            <text id="1">{escape(tip)}</text>
        </binding>
        <binding template="TileWide310x150Text04" fallback="TileWideText04">
            <text id="1">{escape(tip)}</text>
        </binding>
        <binding template="TileSquare310x310ImageAndTextOverlay01">
            <text id="1">{escape(tip)}</text>
        </binding>
    </visual>
</tile>"""
        make_response(health_xml)
        return

    # Sports App Tile
    elif re.search(
        r"en-us\.appex-rf\.msn\.com/cgtile/v1/.+/sports/(?:today|today/(\d+))\.xml",
        url,
        re.IGNORECASE,
    ):
        ctx.log.info(f"Intercepted Sports Tile request for URL: {url}")
        article_index = refresh % 5  # Cycle through 5 sports articles
        match = re.search(r"/sports/today/(\d+)\.xml", url)
        if match:
            try:
                article_index = int(match.group(1))
            except (ValueError, IndexError):
                pass
        make_response(generate_sports_tile(article_index))
        return

    # Food & Drink App Tile
    elif re.search(
        r"en-us\.appex-rf\.msn\.com/cgtile/v1/.+/foodanddrink/(?:today|today/(\d+))\.xml",
        url,
        re.IGNORECASE,
    ):
        ctx.log.info(f"Intercepted Food & Drink Tile request for URL: {url}")
        food_xml = """<tile>
<visual version="2">
<binding template="TileSquare150x150PeekImageAndText04">
<image id="1" src="http://img.s-msn.com//tenant/amp/entityid/AA95gLs_h150_w150_m7.jpg" alt="Baked Eggs in a Ramekin" />
<text id="1">Baked Eggs in a Ramekin</text>
</binding>
<binding template="TileWide310x150PeekImage03">
<image id="1" src="http://img.s-msn.com//tenant/amp/entityid/AA95gLs_h150_w310_m7.jpg" alt="Baked Eggs in a Ramekin" />
<text id="1">Baked Eggs in a Ramekin</text>
</binding>
<binding template="TileSquare310x310ImageAndTextOverlay01">
<image id="1" src="http://img.s-msn.com//tenant/amp/entityid/AA95gLs_h310_w310_m7.jpg" alt="Baked Eggs in a Ramekin" />
<text id="1">Baked Eggs in a Ramekin</text>
</binding>
</visual>
</tile>"""
        make_response(food_xml)
        return

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
