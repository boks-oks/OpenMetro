A mitmproxy script that makes some of Windows 8's Live Tiles work again.
<details>
<summary>Click to show image.</summary>
  
|<img width="1363" height="908" alt="Windows 8.1's Start Screen, showing Finance, News, Games, Food, and Travel tiles, all with modern data." src="https://github.com/user-attachments/assets/bb83052b-a22c-4b80-a798-52dde7d50172" />|
|     :---:      | 
| <i>Not all tiles are working yet, view the list below for deatils</i> |

</details>

<details>
<summary>How does it work?</summary>
  
This diagram should help.
```mermaid
graph TD;
    Windows-->mitmproxy;
    mitmproxy-->RSS;
    RSS-->OpenMetro;
    OpenMetro-->Tile-Data;
    Tile-Data-->Windows;
```
In other words, Windows contacts mitmproxy first, mitmproxy edits the returned data which it gets from OpenMetro parsing RSS feeds.

</details>

# What is/isn't working.

> Did you know I started a blog? Check it out [here](https://boks-oks.github.io/).

#### Tiles
| Tile | Working? |
| ------------- | ------------- |
| News | Complete |
| Food | Complete |
| Finance | Not true to the original. |
| Travel | Complete |
| Games | Complete |
| Health | No |
| Maps | Not in this pre-release. |
| Weather | XML served, tile isn't working. |

#### Apps

> [!NOTE]  
> This states my progress on apps. None are working in the pre-release.

| App | Working? |
| ------------- | ------------- |
| News | No |
| Food | No |
| Finance | No |
| Travel | No |
| Games | No |
| Health | No |
| Maps | Works for a bit, then stops. |
| Weather | Shows served placeholder data, no images. |
