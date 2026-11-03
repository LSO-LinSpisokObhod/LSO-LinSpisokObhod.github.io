# 🚀 LinSpisokObhod

## 📅 Время последнего сбора

`2026-11-03 19:00:15 (UTC+3)`

---

## 📊 Статистика по файлам

| Файл | Всего конфигов |
|------|----------------|
| 📁 ALL.txt / ALL.yml / ALL.json | `446` |
| 📱 LTE.txt / LTE.yml / LTE.json | `50` |
| 📶 WIFI.txt / WIFI.yml / WIFI.json | `396` |

---

## 📡 Статистика по протоколам

### 🌐 ALL

| Протокол | Количество |
|----------|------------|
| 🔗 VLESS | `287` |
| 📦 VMess | `39` |
| 🛡️ Trojan | `111` |
| ⚡ Hysteria2 | `9` |
| **ИТОГО** | **`446`** |

### 📱 LTE

| Протокол | Количество |
|----------|------------|
| 🔗 VLESS | `37` |
| 📦 VMess | `2` |
| 🛡️ Trojan | `11` |
| ⚡ Hysteria2 | `0` |
| **ИТОГО** | **`50`** |

### 📶 WIFI

| Протокол | Количество |
|----------|------------|
| 🔗 VLESS | `250` |
| 📦 VMess | `37` |
| 🛡️ Trojan | `100` |
| ⚡ Hysteria2 | `9` |
| **ИТОГО** | **`396`** |

---

## 🗂️ Фильтрация

1. **fp=chrome** — конфиги с `fp=chrome` **удаляются** для всех протоколов.
2. **LTE** — SNI домен есть в `whitelist.txt` **ИЛИ** IP входит в CIDR из `cidrwhitelist.txt`.
3. **WIFI** — все остальные рабочие конфиги.
4. **ALL** — все конфиги из всех источников.

---

## 📁 Доступные файлы

- `sub/ALL.txt` — URI-список (plain)
- `sub/ALL.yml` — Clash Meta (plain)
- `sub/ALL.json` — sing-box (plain)
- `sub/LTE.txt` / `sub/LTE.yml` / `sub/LTE.json`
- `sub/WIFI.txt` / `sub/WIFI.yml` / `sub/WIFI.json`
- `sub/*.64.txt` — URI-список в base64

---

## 🔄 Автообновление

Скрипт запускается **каждый час**.

---

*LinSpisokObhod v4.2 (Без ESPD)*
