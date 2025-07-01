# OpenMetro

**OpenMetro** is a mitmproxy script that brings Windows 8.1’s Live Tiles back to life using modern APIs.

![Last Updated](https://img.shields.io/badge/Last_Updated-June_26,_2025,_8:10_PM_EST-blue?style=flat-square)

![Screenshot of the Start Screen with 7 live tiles](https://github.com/user-attachments/assets/2daaddaf-3560-4a2f-972f-426cc0167b69)

---

It intercepts tile data requests from apps like News, Weather, and Finance, then feeds them updated info from sources like ESPN or BBC News.  
It’s a preservation + revival project for anyone who misses Live Tiles.
#### For setup instructions, see [here.](./setup.md)

## 🚧 Progress 
![](https://img.shields.io/badge/Tiles%20Revived-All-brightgreen?style=for-the-badge)
| Tile                | Status           | Notes                                      |
|---------------------|------------------|--------------------------------------------|
| **News**            | Complete         | Multiple articles, images.                 |
| **Sports**          | Complete         | Fetches data from ESPN news feed.          |
| **Finance**         | Complete         | CNBC finance RSS.                          |
| **Weather**         | Complete         |Images, location fetched by a local serverⁱ.|
| **Health & Fitness**| Complete         | Images, one article.                       |
| **Food & Drink**    | Complete         | Multiple recipes, images. Uses TheMealDB.  |
| **Travel**          | Complete         | Images from Wikimedia, image titles.       |

ⁱ Location data is used solely to retrieve latitude/longitude for the Weather tile.
This data is never stored or retained.

---

## 🧰 Requirements

- Python 3.x
- [`mitmproxy`](https://mitmproxy.org) (`pip install mitmproxy`)
- A PC or VM running **Windows 8.1**  

---

### 🌐 Sources
> [Badges from shields.io](https://shields.io/)</br>
> [The tile template catalog](https://learn.microsoft.com/en-us/previous-versions/windows/apps/hh761491(v=win.10)).

---

> License: MIT</br>
> Inspired by [Retiled](https://github.com/migbrunluz/Retiled-Win8.x).
