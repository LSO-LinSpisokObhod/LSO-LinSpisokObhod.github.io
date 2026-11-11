# 🚀 LinSpisokObhod

## 📅 Время последнего сбора

`2026-11-11 17:26:44 (UTC+3)`

---

## 📊 Статистика по файлам

| Файл | Всего конфигов |
|------|----------------|
| 📁 ALL.txt / ALL.yml / ALL.json | `492` |
| 📱 LTE.txt / LTE.yml / LTE.json | `35` |
| 📶 WIFI.txt / WIFI.yml / WIFI.json | `457` |

---

## 📡 Статистика по протоколам

### 🌐 ALL

| Протокол | Количество |
|----------|------------|
| 🔗 VLESS | `434` |
| 📦 VMess | `36` |
| 🛡️ Trojan | `19` |
| ⚡ Hysteria2 | `3` |
| **ИТОГО** | **`492`** |

### 📱 LTE

| Протокол | Количество |
|----------|------------|
| 🔗 VLESS | `34` |
| 📦 VMess | `1` |
| 🛡️ Trojan | `0` |
| ⚡ Hysteria2 | `0` |
| **ИТОГО** | **`35`** |

### 📶 WIFI

| Протокол | Количество |
|----------|------------|
| 🔗 VLESS | `400` |
| 📦 VMess | `35` |
| 🛡️ Trojan | `19` |
| ⚡ Hysteria2 | `3` |
| **ИТОГО** | **`457`** |

---

## 🗂️ Фильтрация

1. **fp=chrome → fp=firefox** — все конфиги с `fp=chrome` автоматически переписываются на `fp=firefox` (без удаления).
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
