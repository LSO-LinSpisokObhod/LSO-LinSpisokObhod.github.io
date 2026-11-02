# 🚀 LinSpisokObhod

## 📅 Время последнего сбора

`2026-11-03 01:51:16 (UTC+3)`

---

## 📊 Статистика по файлам

| Файл | Всего конфигов |
|------|----------------|
| 📁 ALL.txt / ALL.yml / ALL.json | `391` |
| 📱 LTE.txt / LTE.yml / LTE.json | `34` |
| 📶 WIFI.txt / WIFI.yml / WIFI.json | `357` |
| 🏫 LinObhodESPD.txt / LinObhodESPD.yml / LinObhodESPD.json | `3` |

---

## 📡 Статистика по протоколам

### 🌐 ALL

| Протокол | Количество |
|----------|------------|
| 🔗 VLESS | `272` |
| 📦 VMess | `31` |
| 🛡️ Trojan | `81` |
| ⚡ Hysteria2 | `7` |
| **ИТОГО** | **`391`** |

### 📱 LTE

| Протокол | Количество |
|----------|------------|
| 🔗 VLESS | `24` |
| 📦 VMess | `1` |
| 🛡️ Trojan | `9` |
| ⚡ Hysteria2 | `0` |
| **ИТОГО** | **`34`** |

### 📶 WIFI

| Протокол | Количество |
|----------|------------|
| 🔗 VLESS | `248` |
| 📦 VMess | `30` |
| 🛡️ Trojan | `72` |
| ⚡ Hysteria2 | `7` |
| **ИТОГО** | **`357`** |

### 🏫 LinObhodESPD

| Протокол | Количество |
|----------|------------|
| 🔗 VLESS | `3` |
| 📦 VMess | `0` |
| 🛡️ Trojan | `0` |
| ⚡ Hysteria2 | `0` |
| **ИТОГО** | **`3`** |

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
