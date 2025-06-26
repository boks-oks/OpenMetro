# OpenMetro

**OpenMetro** is a mitmproxy script that brings Windows 8.1’s Live Tiles back to life using modern APIs.

> [!WARNING]
> I'm reworking the code to OpenMetro. Stay tuned for updates!

![Last Updated](https://img.shields.io/badge/Last_Updated-June_25,_2025,_4:10_PM_EST-blue?style=flat-square)

<!--<details>
<summary>📸 Screenshots</summary>

![LiveTilesStatic](https://github.com/user-attachments/assets/2ffc4aa7-5d50-4523-a0b8-0c2464bd609f)
|:--:| 
| *Live Tiles via OpenMetro* |

![NewsTileUpdate](https://github.com/user-attachments/assets/65d9a13e-cdd4-4d71-8abb-e23f3204b9be)
|:--:| 
| *A Live Tile updating via OpenMetro.* |

> Images are out of date. Updated images will be uploaded once most bugs are ironed out.

</details>-->

---

It intercepts tile data requests from apps like News, Weather, and Finance, then feeds them updated info from sources like ESPN or BBC News.  
It’s a preservation + revival project for anyone who misses Live Tiles.
#### For setup instructions, see [here.](./setup.md)

## 🚧 Rework Progress 
![](https://img.shields.io/badge/Tiles%20Revived-4/7-yellow?style=for-the-badge)
| Tile                | Status           | Notes                                      |
|---------------------|------------------|--------------------------------------------|
| **News**            | Complete         | Multiple articles, images.                 |
| **Sports**          | Incomplete       |                                            |
| **Finance**         | Incomplete       |                                            |
| **Weather**         | Complete         |Images, locally hosted siteⁱ grabs location.|
| **Health & Fitness**| Complete         | Images, one article.                       |
| **Food & Drink**    | Complete         | Multiple recipes, images. Uses TheMealDB   |
| **Travel**          | Incomplete       |                                            |

ⁱ Location data is used only for getting the lat/long for the Weather tile, nothing else.
<!--
![Apps Revived: None yet](https://img.shields.io/badge/Apps%20Revived%3A-None_yet-darkred?style=for-the-badge)
| App                  | Planned?         | Status / Notes                                 |
|----------------------|------------------|------------------------------------------------|
| **News**             | 🟢 Definitely     | Needs research into request/response format    |
| **Sports**           | 🟢 Definitely     | Same as above                                  |
| **Finance**          | 🟢 Definitely     | Same as above                                  |
| **Weather**          | 🟡 Maybe          | Format unknown                                 |
| **Health & Fitness** | 🟢 Definitely     | Not a current priority                         |
| **Food & Drink**     | 🟡 Maybe          | Not a current priority                         |
| **Windows Store**    | 🟠 Maybe          | Low priority – requires extensive reverse engineering |
I'll come back to this.
-->
---

![Apps](https://img.shields.io/badge/Apps:-At_a_later_date-black?style=for-the-badge)

| App                  | Planned?             | Status / Notes                          |
|----------------------|----------------------|-----------------------------------------|
| **News**             | At a later date.     |  None                                   |
| **Sports**           | At a later date.     |  None                                   |
| **Finance**          | At a later date.     |  None                                   |
| **Weather**          | At a later date.     |  None                                   |
| **Health & Fitness** | At a later date.     |  None                                   |
| **Food & Drink**     | At a later date.     |  None                                   |
| **Calendar/Mail**    | At a later date.     |  None                                   |
| **Windows Store**    | At a later date.     |  None                                   |
---

## 🧰 Requirements

- Python 3.x
- [`mitmproxy`](https://mitmproxy.org) (`pip install mitmproxy`)
- A PC or VM running **Windows 8.1**  
  *(Only tested with Start screen Live Tiles.)*

---

## 🎯 Goals

### Main Goals
- [x]  **Live Tile** functionality
- [ ] **Revive most Metro apps**, including their Live Tiles
- [ ] **Windows Store revival**
  - [ ] Serve custom Metro-style apps via proxy
  - [ ] Support viewing (but not purchasing) paid or unavailable apps

---
### 🌐 Sources
> [Badges from shields.io](https://shields.io/)</br>
> [Analysis of `http://en-US.appex-rf.msn.com/cgtile/v1/en-US/News/Today.xml` on any.run](https://any.run/report/0170ceadd75b172e238c8c1c4cd1ab8d6df5aefde999733295ccf57d007630ea/c1ed3fbc-4ea6-4d0f-ac4b-12580eeb9f32)<br/>
> [The tile template catalog](https://learn.microsoft.com/en-us/previous-versions/windows/apps/hh761491(v=win.10)).
---

![](https://img.shields.io/badge/Mentioned%20by-Copilot-blueviolet?style=for-the-badge)
|:--:| 
| *I’m not even joking, try it for yourself!* |

---
> License: MIT</br>
> OpenMetro is still in development and may contain bugs.</br>
> OpenMetro is inspired by [Retiled](https://github.com/migbrunluz/Retiled-Win8.x).
