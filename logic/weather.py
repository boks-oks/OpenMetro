import datetime
from urllib.parse import parse_qs, urlparse
import requests
from mitmproxy import http

ASSETMAP = {
    "01d": {
        "background": "https://vortex.accuweather.com/adc2010/hostedpages/w8api/bg310x310/01_02.jpg",
        "icon":       "https://vortex.accuweather.com/adc2010/hostedpages/w8api/icons80x80/01.png"
    },
    "01n": {
        "background": "https://vortex.accuweather.com/adc2010/hostedpages/w8api/bg310x310/33.jpg",
        "icon":       "https://vortex.accuweather.com/adc2010/hostedpages/w8api/icons80x80/33.png"
    },
    "04n": {
        "background": "https://vortex.accuweather.com/adc2010/hostedpages/w8api/bg310x310/33.jpg",
        "icon":       "https://vortex.accuweather.com/adc2010/hostedpages/w8api/icons80x80/33.png"
    },
    "04d": {
        "background": "https://vortex.accuweather.com/adc2010/hostedpages/w8api/bg310x310/11.jpg",
        "icon":       "https://vortex.accuweather.com/adc2010/hostedpages/w8api/icons80x80/11.png"
    },
    "02d": {
        "background": "https://vortex.accuweather.com/adc2010/hostedpages/w8api/bg310x310/03_04_05.jpg",
        "icon":       "https://vortex.accuweather.com/adc2010/hostedpages/w8api/icons80x80/03.png"
    },
    "02n": {
        "background": "https://vortex.accuweather.com/adc2010/hostedpages/w8api/bg310x310/38.jpg",
        "icon":       "https://vortex.accuweather.com/adc2010/hostedpages/w8api/icons80x80/38.png"
    },
    "03d": {
        "background": "https://vortex.accuweather.com/adc2010/hostedpages/w8api/bg310x310/03_04_05.jpg",
        "icon":       "https://vortex.accuweather.com/adc2010/hostedpages/w8api/icons80x80/03.png"
    },
    "03n": {
        "background": "https://vortex.accuweather.com/adc2010/hostedpages/w8api/bg310x310/30_31_32_34_35_36_37.jpg",
        "icon":       "https://vortex.accuweather.com/adc2010/hostedpages/w8api/icons80x80/30.png"
    },
    "09d": {
        "background": "https://vortex.accuweather.com/adc2010/hostedpages/w8api/bg310x310/12_13_39_40.jpg",
        "icon":       "https://vortex.accuweather.com/adc2010/hostedpages/w8api/icons80x80/12.png"
    },
    "09n": {
        "background": "https://vortex.accuweather.com/adc2010/hostedpages/w8api/bg310x310/24_25_26.jpg",
        "icon":       "https://vortex.accuweather.com/adc2010/hostedpages/w8api/icons80x80/24.png"
    },
    "10d": {
        "background": "https://vortex.accuweather.com/adc2010/hostedpages/w8api/bg310x310/14.jpg",
        "icon":       "https://vortex.accuweather.com/adc2010/hostedpages/w8api/icons80x80/14.png"
    },
    "10n": {
        "background": "https://vortex.accuweather.com/adc2010/hostedpages/w8api/bg310x310/18.jpg",
        "icon":       "https://vortex.accuweather.com/adc2010/hostedpages/w8api/icons80x80/18.png"
    },
    "11d": {
        "background": "https://vortex.accuweather.com/adc2010/hostedpages/w8api/bg310x310/15_41_42.jpg",
        "icon":       "https://vortex.accuweather.com/adc2010/hostedpages/w8api/icons80x80/15.png"
    },
    "11n": {
        "background": "https://vortex.accuweather.com/adc2010/hostedpages/w8api/bg310x310/24_25_26.JPG",
        "icon":       "https://vortex.accuweather.com/adc2010/hostedpages/w8api/icons80x80/24.png"
    },
    "13d": {
        "background": "https://vortex.accuweather.com/adc2010/hostedpages/w8api/bg310x310/19_43.jpg",
        "icon":       "https://vortex.accuweather.com/adc2010/hostedpages/w8api/icons80x80/19.png"
    },
    "13n": {
        "background": "https://vortex.accuweather.com/adc2010/hostedpages/w8api/bg310x310/29.jpg",
        "icon":       "https://vortex.accuweather.com/adc2010/hostedpages/w8api/icons80x80/29.png"
    },
    "50d": {
        "background": "https://vortex.accuweather.com/adc2010/hostedpages/w8api/bg310x310/31.jpg",
        "icon":       "https://vortex.accuweather.com/adc2010/hostedpages/w8api/icons80x80/31.png"
    },
    "50n": {
        "background": "https://vortex.accuweather.com/adc2010/hostedpages/w8api/bg310x310/11.jpg",
        "icon":       "https://vortex.accuweather.com/adc2010/hostedpages/w8api/icons80x80/11.png"
    }
}


WMO_WEATHER_DESCRIPTIONS = {0:"Clear sky",1:"Mainly clear",2:"Partly cloudy",3:"Overcast",45:"Fog",48:"Depositing rime fog",51:"Light drizzle",53:"Moderate drizzle",55:"Dense drizzle",56:"Light freezing drizzle",57:"Dense freezing drizzle",61:"Slight rain",63:"Moderate rain",65:"Heavy rain",66:"Light freezing rain",67:"Heavy freezing rain",71:"Slight snow fall",73:"Moderate snow fall",75:"Heavy snow fall",77:"Snow grains",80:"Slight rain showers",81:"Moderate rain showers",82:"Violent rain showers",85:"Slight snow showers",86:"Heavy snow showers",95:"Thunderstorm",96:"Thunderstorm with slight hail",99:"Thunderstorm with heavy hail"}
WMO_TO_MSN_ACCUWEATHER_CODE = {0:"01",1:"01",2:"02",3:"04",45:"50",48:"50",51:"09",53:"09",55:"09",56:"10",57:"10",61:"10",63:"10",65:"10",66:"10",67:"10",71:"13",73:"13",75:"13",77:"13",80:"09",81:"09",82:"09",85:"13",86:"13",95:"11",96:"11",99:"11"}

tile = """
<tile>
  <visual version="2">
    <binding template="TileSquare150x150Block" fallback="TileSquareBlock">
      <text id="1">{temp}</text>
      <text id="2">{location_short_name}</text>
    </binding>  
    <binding template="TileWide310x150SmallImageAndText04" fallback="TileWideSmallImageAndText04">
      <image id="1" src="{icon}" alt="alt text"/>
      <text id="1">{location_long_name}</text>
      <text id="2">It is currently {temp} outside. Last updated on {full_time}.</text>
    </binding>
    <binding template="TileSquare310x310BlockAndText02">
      <image id="1" src="{img}" alt="alt text"/>
      <text id="1">{temp}</text>
      <text id="2">{location_short_name}</text>
      <text id="3">{conditions} {hi_lo}</text>
      <text id="4"></text>
      <text id="5"></text>
      <text id="6"></text>
      <text id="7"></text>
    </binding>  
  </visual>
</tile>
"""

def format_tile_template(weather_data, location_info, time_info):    
    if not location_info.get('short_name') or not location_info.get('long_name'):
        lat = weather_data.get('latitude')
        lon = weather_data.get('longitude')
        if lat is not None and lon is not None:
            location_info = reverse_geocode(lat, lon)

    current = weather_data['current']
    daily = weather_data['daily']
    
    weather_code = str(current['weather_code'])
    is_day = current['is_day']
    day_night = 'd' if is_day else 'n'
    
    accuweather_code = WMO_TO_MSN_ACCUWEATHER_CODE.get(int(weather_code), "01")
    assets = ASSETMAP.get(f"{accuweather_code}{day_night}")
    bg_url = assets["background"]
    icon_url = assets["icon"]

    return tile.format(
        temp=f"{int(current['temperature_2m'])}°F",
        location_short_name=location_info.get('short_name', 'Unknown'),
        location_long_name=location_info.get('long_name', 'Unknown Location'),
        img=bg_url,
        icon=icon_url,
        full_time=time_info.get('current_time', 'Unknown Time'),
        conditions=WMO_WEATHER_DESCRIPTIONS.get(int(weather_code), "Unknown"),
        hi_lo=f"Hi: {int(daily['temperature_2m_max'][0])}°F Lo: {int(daily['temperature_2m_min'][0])}°F"
    )

def reverse_geocode(lat, lon):
    url = "https://nominatim.openstreetmap.org/reverse"
    params = {
        "format": "json",
        "lat": lat,
        "lon": lon,
        "zoom": 10,
        "addressdetails": 1
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        addr = data.get("address", {})
        short_name = addr.get("city") or addr.get("town") or addr.get("village") or "Unknown"
        long_name = data.get("display_name", "Unknown Location")
        return {"short_name": short_name, "long_name": long_name}
    except Exception:
        return {"short_name": "Unknown", "long_name": "Unknown Location"}

def get_openmeteo_data(lat, lon):
    base = "https://api.open-meteo.com/v1/forecast"
    params = {"latitude": lat, "longitude": lon, "current": "temperature_2m,weather_code,is_day", "daily": "temperature_2m_max,temperature_2m_min,weather_code", "timezone": "EST", "forecast_days": 2, "temperature_unit": "fahrenheit"}    
    return requests.get(base, params=params).json()

def readable_datetime(iso_time_str):
    dt = datetime.datetime.strptime(iso_time_str, "%Y-%m-%dT%H:%M")
    return dt.strftime("%B %d, %Y at %I:%M %p")

def map_weather_code(code):
    assets = ASSETMAP.get(code)
    if assets:
        return assets
    else:
        # Fallback if the weather code isn't mapped
        return {
            "background": "https://placehold.co/310x310/blue/black/png?text=?",
            "icon": "https://placehold.co/80x80/blue/black/png?text=?"
        }
import requests

def get_location_info(lat, lon):
    url = "https://nominatim.openstreetmap.org/reverse"
    params = {
        "format": "json",
        "lat": lat,
        "lon": lon,
        "zoom": 10,            # level of detail (10 = city/region)
        "addressdetails": 1
    }
    headers = {"User-Agent": "OpenMetro/1.2"}

    try:
        resp = requests.get(url, params=params, headers=headers, timeout=5)
        if resp.status_code != 200:
            # fallback short/long as unknown
            return {"short_name": "Unknown", "long_name": "Unknown Location"}
        data = resp.json()
        addr = data.get("address", {})

        # prefer city/town/village, fallback to county/state, finally country
        short = addr.get("city") or addr.get("town") or addr.get("village") \
                or addr.get("municipality") or addr.get("county") or addr.get("state") \
                or addr.get("country") or "Unknown"

        # make a compact long name like "City, Country" or "Region, Country"
        country = addr.get("country")
        region = addr.get("state") or addr.get("county") or addr.get("region")
        if short != "Unknown" and country:
            long = f"{short}, {country}"
        elif region and country:
            long = f"{region}, {country}"
        else:
            long = data.get("display_name", "Unknown Location")

        return {"short_name": short, "long_name": long}
    except Exception as e:
        # network timeout / parse error returns a fallback
        print("Reverse geocode failed:", e)
        return {"short_name": "Unknown", "long_name": "Unknown Location"}

def get_lat_lon_from_url(url):
    parsed = urlparse(url)
    qs = parse_qs(parsed.query)
    # parse_qs returns values as lists, so grab first item or None
    lat = qs.get('lat', [None])[0]
    lon = qs.get('long', [None])[0]  # note param name is 'long' not 'lon'
    return lat, lon

def main(flow: http.HTTPFlow):
    lat, lon = get_lat_lon_from_url(flow.request.url)
    location_info = get_location_info(lat, lon)
    if lat is not None and lon is not None:
        weather_data = get_openmeteo_data(lat, lon)
    else:
        # fallback coords of new york city.
        weather_data = get_openmeteo_data(40.7128, -74.0060)

    iso_time = weather_data['current']['time']
    time_info = {
        "current_time": readable_datetime(iso_time)
    }

    tile_xml = format_tile_template(weather_data, location_info, time_info)
    return tile_xml












"""
This code looks so AI. It's not, trust me.
I guess it's just because it's so... long.
I really never write code this long, but I kind of have to here.
"""