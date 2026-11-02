# 🚀 LinSpisokObhod

## 📅 Время последнего сбора

`2026-11-02 20:12:17 (UTC+3)`

---

## 📊 Статистика по файлам

| Файл | Всего конфигов |
|------|----------------|
| 📁 ALL.txt / ALL.yml / ALL.json | `423` |
| 📱 LTE.txt / LTE.yml / LTE.json | `32` |
| 📶 WIFI.txt / WIFI.yml / WIFI.json | `391` |
| 🏫 LinObhodESPD.txt / LinObhodESPD.yml / LinObhodESPD.json | `1` |

---

## 📡 Статистика по протоколам

### 🌐 ALL

| Протокол | Количество |
|----------|------------|
| 🔗 VLESS | `299` |
| 📦 VMess | `34` |
| 🛡️ Trojan | `87` |
| ⚡ Hysteria2 | `3` |
| **ИТОГО** | **`423`** |

### 📱 LTE

| Протокол | Количество |
|----------|------------|
| 🔗 VLESS | `19` |
| 📦 VMess | `5` |
| 🛡️ Trojan | `8` |
| ⚡ Hysteria2 | `0` |
| **ИТОГО** | **`32`** |

### 📶 WIFI

| Протокол | Количество |
|----------|------------|
| 🔗 VLESS | `280` |
| 📦 VMess | `29` |
| 🛡️ Trojan | `79` |
| ⚡ Hysteria2 | `3` |
| **ИТОГО** | **`391`** |

### 🏫 LinObhodESPD

| Протокол | Количество |
|----------|------------|
| 🔗 VLESS | `1` |
| 📦 VMess | `0` |
| 🛡️ Trojan | `0` |
| ⚡ Hysteria2 | `0` |
| **ИТОГО** | **`1`** |

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
