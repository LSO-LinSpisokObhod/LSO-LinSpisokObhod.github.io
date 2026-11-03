# 🚀 LinSpisokObhod

## 📅 Время последнего сбора

`2026-11-03 23:56:27 (UTC+3)`

---

## 📊 Статистика по файлам

| Файл | Всего конфигов |
|------|----------------|
| 📁 ALL.txt / ALL.yml / ALL.json | `493` |
| 📱 LTE.txt / LTE.yml / LTE.json | `52` |
| 📶 WIFI.txt / WIFI.yml / WIFI.json | `441` |

---

## 📡 Статистика по протоколам

### 🌐 ALL

| Протокол | Количество |
|----------|------------|
| 🔗 VLESS | `327` |
| 📦 VMess | `37` |
| 🛡️ Trojan | `123` |
| ⚡ Hysteria2 | `6` |
| **ИТОГО** | **`493`** |

### 📱 LTE

| Протокол | Количество |
|----------|------------|
| 🔗 VLESS | `41` |
| 📦 VMess | `1` |
| 🛡️ Trojan | `10` |
| ⚡ Hysteria2 | `0` |
| **ИТОГО** | **`52`** |

### 📶 WIFI

| Протокол | Количество |
|----------|------------|
| 🔗 VLESS | `286` |
| 📦 VMess | `36` |
| 🛡️ Trojan | `113` |
| ⚡ Hysteria2 | `6` |
| **ИТОГО** | **`441`** |

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
