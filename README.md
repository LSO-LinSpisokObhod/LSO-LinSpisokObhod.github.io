# 🚀 LinSpisokObhod

## 📅 Время последнего сбора

`2026-11-04 16:32:23 (UTC+3)`

---

## 📊 Статистика по файлам

| Файл | Всего конфигов |
|------|----------------|
| 📁 ALL.txt / ALL.yml / ALL.json | `504` |
| 📱 LTE.txt / LTE.yml / LTE.json | `48` |
| 📶 WIFI.txt / WIFI.yml / WIFI.json | `456` |

---

## 📡 Статистика по протоколам

### 🌐 ALL

| Протокол | Количество |
|----------|------------|
| 🔗 VLESS | `378` |
| 📦 VMess | `34` |
| 🛡️ Trojan | `87` |
| ⚡ Hysteria2 | `5` |
| **ИТОГО** | **`504`** |

### 📱 LTE

| Протокол | Количество |
|----------|------------|
| 🔗 VLESS | `36` |
| 📦 VMess | `1` |
| 🛡️ Trojan | `11` |
| ⚡ Hysteria2 | `0` |
| **ИТОГО** | **`48`** |

### 📶 WIFI

| Протокол | Количество |
|----------|------------|
| 🔗 VLESS | `342` |
| 📦 VMess | `33` |
| 🛡️ Trojan | `76` |
| ⚡ Hysteria2 | `5` |
| **ИТОГО** | **`456`** |

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
