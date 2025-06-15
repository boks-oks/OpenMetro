# OpenMetro

**OpenMetro** is a mitmproxy script that brings Windows 8.1’s Live Tiles back to life using modern APIs.

![LiveTilesStatic](https://github.com/user-attachments/assets/e841257e-49e6-4e9c-ada6-16b71a32fa4c)
|:--:| 
| *Live Tiles using OpenMetro* |

It intercepts tile data requests from apps like News, Weather, and Finance, then feeds them updated info from sources like ESPN or BBC News.  
It’s a preservation + revival project for anyone who misses headlines and stock updates on their Start screen.

![NewsTileGIF](https://github.com/user-attachments/assets/14b3bca8-657a-400b-b1e6-098d86d20c56)
|:--:| 
| *A Live Tile updating using OpenMetro.* |

> [!NOTE]
> Currently, only **Live Tile data** is being restored — the full apps themselves are not functional through this proxy yet.

---

## 🚧 Progress

### Tiles

| Tile                | Status             | Notes                                  |
|---------------------|--------------------|----------------------------------------|
| **News**            | ✅ Mostly complete  | Multiple articles, no images (yet)     |
| **Sports**          | 🔄 In progress      | Placeholder data only                  |
| **Finance**         | ✅ Mostly complete  | One article only, no images            |
| **Weather**         | ❓ Unknown          | Uses an obscure format                 |
| **Health & Fitness**| ❓ Unknown          | Appears similar to Weather             |
| **Food & Drink**    | ❓ Unknown          | Similar structure to Weather           |
| **Calendar/Mail**   | 🚫 Not implemented | Requires Microsoft Account authentication |

---

### Apps

| App                  | Will Be Revived? | Status / Notes                                 |
|----------------------|------------------|------------------------------------------------|
| **News**             | ❗ Definitely     | Needs research into request/response format    |
| **Sports**           | ❗ Definitely     | Same as above                                  |
| **Finance**          | ❗ Definitely     | Same as above                                  |
| **Weather**          | ❓ Maybe          | Format unknown — will explore                  |
| **Health & Fitness** | ❗ Definitely     | Not a current priority                         |
| **Food & Drink**     | ❓ Maybe          | Not a current priority                         |
| **Calendar/Mail**    | 🚫 No            | Requires Microsoft Account auth                |
| **Windows Store**    | ⁉️ Maybe         | Low priority – requires extensive reverse engineering |

---

## 🧰 Requirements

- Python 3.x
- [`mitmproxy`](https://mitmproxy.org) (`pip install mitmproxy`)
- A PC or VM running **Windows 8.1**  
  *(Only tested with Start screen Live Tiles. Other OSes not supported.)*

📦 See [setup.md](./setup.md) for installation and proxy configuration.

---
---

## 🎯 Goals

### Main Goals
- [x] **Basic Live Tile functionality**
- [ ] ✅ **Revive most Metro apps**, including their Live Tiles
- [ ] 🛠️ **Create an installer** (`.EXE` or `.MSI`) for easy setup
- [ ] 🖥️ **Build a GUI**
  - [ ] Show revival status
  - [ ] Enable/disable specific revived Metro apps
- [ ] 🏬 **Windows Store revival**
  - [ ] Serve custom Metro-style apps via proxy
  - [ ] Support viewing (but not purchasing) paid or unavailable apps

### Bonus / Stretch Goals
- [ ] ✉️ **Bypass Microsoft Account authentication** for Calendar/Mail *(if possible)*

---

## 📜 License

**MIT** – use freely, modify wildly, and please don’t sue me.
