# OpenMetro

**OpenMetro** is a mitmproxy script that brings Windows 8.1’s Live Tiles back to life using modern APIs.

<details>
<summary>📸 Screenshots</summary>

![LiveTilesStatic](https://github.com/user-attachments/assets/2ffc4aa7-5d50-4523-a0b8-0c2464bd609f)
|:--:| 
| *Live Tiles via OpenMetro* |

![NewsTileUpdate](https://github.com/user-attachments/assets/65d9a13e-cdd4-4d71-8abb-e23f3204b9be)
|:--:| 
| *A Live Tile updating via OpenMetro.* |

</details>

It intercepts tile data requests from apps like News, Weather, and Finance, then feeds them updated info from sources like ESPN or BBC News.  
It’s a preservation + revival project for anyone who misses Live Tiles on the Start Screen.

> For setup instructions, see [here.](./setup.md)

> [!NOTE]
> Currently, only **Live Tile data** is being restored — the full apps themselves are not functional through this proxy yet.

---

## Why "OpenMetro"?

"Metro" refers to the bold, typography-focused design language used in Windows 8.x.

"Open" reflects the spirit of open-source — anyone can view, use, and contribute to the project.

---

## 🚧 Progress 
![](https://img.shields.io/badge/Tiles%20Revived-All%2F7-brightgreen)
##### Tiles are Start Screen visuals powered by XML and local data.

| Tile                | Status             | Notes                                      |
|---------------------|--------------------|--------------------------------------------|
| **News**            | 🟢 Complete         | Multiple articles, images                  |
| **Sports**          | 🟢 Complete         | One article, images                        |
| **Finance**         | 🟢 Complete         | Multiple articles, no images               |
| **Weather**         | 🟢 Complete         | Weather data, GeoIP                        |
| **Health & Fitness**| 🟢 Complete         | Shows a tip or fact from a predefined list |
| **Food & Drink**    | 🟢 Complete         | Receives recipes from themealdb            |
| **Calendar/Mail**   | 🔴 Not planned      | Requires Microsoft Account authentication  |


![Apps Revived: None yet](https://img.shields.io/badge/Apps%20Revived%3A-None_yet-darkred)

##### Apps are full-screen Metro applications requiring deeper reverse engineering and data proxying.
| App                  | Planned?         | Status / Notes                                 |
|----------------------|------------------|------------------------------------------------|
| **News**             | 🟢 Definitely     | Needs research into request/response format    |
| **Sports**           | 🟢 Definitely     | Same as above                                  |
| **Finance**          | 🟢 Definitely     | Same as above                                  |
| **Weather**          | 🟡 Maybe          | Format unknown                                 |
| **Health & Fitness** | 🟢 Definitely     | Not a current priority                         |
| **Food & Drink**     | 🟡 Maybe          | Not a current priority                         |
| **Calendar/Mail**    | 🔴 Not planned    | Requires Microsoft Account authentication      |
| **Windows Store**    | 🟠 Maybe          | Low priority – requires extensive reverse engineering |

---

| Key                  |                                  |
|----------------------|----------------------------------|
| 🟢 Complete          | Fully revived and functional     |
| 🟡 Unknown/Maybe     | Investigating feasibility        |
| 🔴 Not planned       | Currently not practical          |
| 🟠 Maybe             | Could be done, but not a priority|

---

## 🧰 Requirements

- Python 3.x
- [`mitmproxy`](https://mitmproxy.org) (`pip install mitmproxy`)
- A PC or VM running **Windows 8.1**  
  *(Only tested with Start screen Live Tiles.)*

---

## 🎯 Goals

### Main Goals
- [x] **Basic** Live Tile functionality
  - [x] Weather
  - [x] News
  - [x] Finance
  - [x] Sports
- [ ] **Full** Live Tile functionality
  - [x] Weather
  - [x] News
  - [x] Finance
  - [x] Sports
- [ ] ✅ **Revive most Metro apps**, including their Live Tiles
- [ ] 🛠️ **Create an installer** (`.EXE` or `.MSI`) for easy setup
- [ ] 🖥️ **Build a GUI**
  - [ ] Show revival status
  - [ ] Enable/disable specific revived Metro apps
- [ ] 🏬 **Windows Store revival**
  - [ ] Serve custom Metro-style apps via proxy
  - [ ] Support viewing (but not purchasing) paid or unavailable apps

---
##### Please note that OpenMetro is still in development and may contain bugs.
---
### 🌐 Sources
##### [Badges from shields.io](https://shields.io/)
##### [Analysis of `http://en-US.appex-rf.msn.com/cgtile/v1/en-US/News/Today.xml` on any.run](https://any.run/report/0170ceadd75b172e238c8c1c4cd1ab8d6df5aefde999733295ccf57d007630ea/c1ed3fbc-4ea6-4d0f-ac4b-12580eeb9f32)
---

![](https://img.shields.io/badge/Mentioned%20by-Copilot-blueviolet?logo=microsoft) 
|:--:| 
| *I’m not even joking, try it for yourself!* |

---
## 📜 License: MIT
