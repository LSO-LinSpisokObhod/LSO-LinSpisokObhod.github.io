# 🚀 LinSpisokObhod

## 📅 Время последнего сбора

`2026-11-04 20:03:01 (UTC+3)`

---

## 📊 Статистика по файлам

| Файл | Всего конфигов |
|------|----------------|
| 📁 ALL.txt / ALL.yml / ALL.json | `485` |
| 📱 LTE.txt / LTE.yml / LTE.json | `42` |
| 📶 WIFI.txt / WIFI.yml / WIFI.json | `443` |

---

## 📡 Статистика по протоколам

### 🌐 ALL

| Протокол | Количество |
|----------|------------|
| 🔗 VLESS | `359` |
| 📦 VMess | `35` |
| 🛡️ Trojan | `86` |
| ⚡ Hysteria2 | `5` |
| **ИТОГО** | **`485`** |

### 📱 LTE

| Протокол | Количество |
|----------|------------|
| 🔗 VLESS | `30` |
| 📦 VMess | `1` |
| 🛡️ Trojan | `11` |
| ⚡ Hysteria2 | `0` |
| **ИТОГО** | **`42`** |

### 📶 WIFI

| Протокол | Количество |
|----------|------------|
| 🔗 VLESS | `329` |
| 📦 VMess | `34` |
| 🛡️ Trojan | `75` |
| ⚡ Hysteria2 | `5` |
| **ИТОГО** | **`443`** |

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
