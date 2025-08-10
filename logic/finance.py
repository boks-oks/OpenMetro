# This one is CSV.
import csv
import json
import os
import requests
from io import StringIO

import urllib

url = "https://stooq.com/q/d/l/?s=MSFT.US&i=d"
"""
Stooq returns data as follows: 
Date,Open,High,Low,Close,Volume
2025-07-23,506.75,506.79,500.7,505.87,16396585
2025-07-24,508.77,513.67,507.3,510.88,16107000
2025-07-25,512.465,518.29,510.3592,513.71,19125699
2025-07-28,514.08,515,510.12,512.5,14308027
2025-07-29,515.53,517.62,511.56,512.57,16469235
2025-07-30,515.17,515.95,509.435,509.945,7184486

I return it in a simple format:
↑ 0.05%
↓ -0.02%

We'll also return a graph from quickchart.io.
"""

def fetch_stock_data(url):
    response = requests.get(url)
    if response.status_code == 200:
        csv_data = StringIO(response.text)
        reader = csv.DictReader(csv_data)
        stock_data = [row for row in reader]
        return stock_data


def format_stock_data(stock_data):
    if not stock_data:
        return "No data available"
    
    latest_data = stock_data[-1]
    previous_data = stock_data[-2] if len(stock_data) > 1 else latest_data
    
    latest_close = float(latest_data['Close'])
    previous_close = float(previous_data['Close'])
    
    change = latest_close - previous_close
    percentage_change = (change / previous_close) * 100
    
    if change > 0:
        return f"MSFT: ↑ {percentage_change:.2f}%"
    elif change < 0:
        return f"MSFT: ↓ {percentage_change:.2f}%"
    else:
        return "No change"
    
def generate_graph_url(stock_data):
    if not stock_data or len(stock_data) < 5:
        return "No data available for graph"
    
    # Previous 5 days.
    latest_data = stock_data[-1]
    previous_data = stock_data[-2]
    before_previous_data = stock_data[-3]
    before_before_previous_data = stock_data[-4]
    before_before_before_previous_data = stock_data[-5]

    latest_close = float(latest_data['Close'])
    previous_close = float(previous_data['Close'])
    before_previous_close = float(before_previous_data['Close'])
    before_before_previous_close = float(before_before_previous_data['Close'])
    before_before_before_previous_close = float(before_before_before_previous_data['Close'])

    # Hey, what was I supposed to name those variables?  I mean, come on, you expect me to name them something that's not just "before_before_before_previous_close"?

    color = "green" if latest_close > previous_close else "red"

    prices = [before_before_before_previous_close, before_before_previous_close, before_previous_close, previous_close, latest_close]

    config = {
        "type": "sparkline",
        "data": {
            "datasets": [{
                "data": prices,
                "borderColor": f"{color}",
                "borderWidth": 5,
                "fill": False
            }]
        },
        "options": {
            "elements": {
                "line": {"tension": 0.3},
                "point": {"radius": 0}
            },
        }
    }

    config_str = json.dumps(config, separators=(",", ":"))
    encoded = urllib.parse.quote(config_str, safe="")
    chart_url = f"https://quickchart.io/chart?c={encoded}&backgroundColor=transparent&width=248&height=200"

    return chart_url

def main():
    stock_data = fetch_stock_data(url)
    formatted_data = format_stock_data(stock_data)
    graph_url = generate_graph_url(stock_data)

    with open(os.path.join("tile", "finance.xml"), "r") as f:
        xml_content = f.read()

    xml_content = xml_content.replace("{symupdn}", formatted_data)
    xml_content = xml_content.replace("{graphimage}", graph_url)

    # Escape &
    xml_content = xml_content.replace('&', '&amp;')

    return xml_content