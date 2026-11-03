# 🚀 LinSpisokObhod

## 📅 Время последнего сбора

`2026-11-03 04:12:17 (UTC+3)`

---

## 📊 Статистика по файлам

| Файл | Всего конфигов |
|------|----------------|
| 📁 ALL.txt / ALL.yml / ALL.json | `426` |
| 📱 LTE.txt / LTE.yml / LTE.json | `39` |
| 📶 WIFI.txt / WIFI.yml / WIFI.json | `387` |
| 🏫 LinObhodESPD.txt / LinObhodESPD.yml / LinObhodESPD.json | `2` |

---

## 📡 Статистика по протоколам

### 🌐 ALL

| Протокол | Количество |
|----------|------------|
| 🔗 VLESS | `304` |
| 📦 VMess | `33` |
| 🛡️ Trojan | `84` |
| ⚡ Hysteria2 | `5` |
| **ИТОГО** | **`426`** |

### 📱 LTE

| Протокол | Количество |
|----------|------------|
| 🔗 VLESS | `28` |
| 📦 VMess | `2` |
| 🛡️ Trojan | `9` |
| ⚡ Hysteria2 | `0` |
| **ИТОГО** | **`39`** |

### 📶 WIFI

| Протокол | Количество |
|----------|------------|
| 🔗 VLESS | `276` |
| 📦 VMess | `31` |
| 🛡️ Trojan | `75` |
| ⚡ Hysteria2 | `5` |
| **ИТОГО** | **`387`** |

### 🏫 LinObhodESPD

| Протокол | Количество |
|----------|------------|
| 🔗 VLESS | `2` |
| 📦 VMess | `0` |
| 🛡️ Trojan | `0` |
| ⚡ Hysteria2 | `0` |
| **ИТОГО** | **`2`** |

---

## 🗂️ Фильтрация

1. **fp=chrome** — конфиги с `fp=chrome` **удаляются** для всех протоколов.
2. **LTE** — SNI домен есть в `whitelist.txt` **ИЛИ** IP входит в CIDR из `cidrwhitelist.txt`.
3. **WIFI** — все остальные рабочие конфиги.
4. **LinObhodESPD** — конфиги с SNI `max.ru` или `api-maps.yandex.ru`.
5. **ALL** — все конфиги из всех источников.

---

## 📁 Доступные файлы

- `sub/ALL.txt` — URI-список (plain)
- `sub/ALL.yml` — Clash Meta (plain)
- `sub/ALL.json` — sing-box (plain)
- `sub/LTE.txt` / `sub/LTE.yml` / `sub/LTE.json`
- `sub/WIFI.txt` / `sub/WIFI.yml` / `sub/WIFI.json`
- `sub/LinObhodESPD.txt` / `sub/LinObhodESPD.yml` / `sub/LinObhodESPD.json`
- `sub/*.64.txt` — URI-список в base64

---

## 🔄 Автообновление

Скрипт запускается **каждый час**.

---

*LinSpisokObhod v4.0 (YAML + JSON, no .64 for yml/json)*
