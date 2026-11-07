# 🚀 LinSpisokObhod

## 📅 Время последнего сбора

`2026-11-07 05:56:43 (UTC+3)`

---

## 📊 Статистика по файлам

| Файл | Всего конфигов |
|------|----------------|
| 📁 ALL.txt / ALL.yml / ALL.json | `414` |
| 📱 LTE.txt / LTE.yml / LTE.json | `27` |
| 📶 WIFI.txt / WIFI.yml / WIFI.json | `387` |

---

## 📡 Статистика по протоколам

### 🌐 ALL

| Протокол | Количество |
|----------|------------|
| 🔗 VLESS | `352` |
| 📦 VMess | `36` |
| 🛡️ Trojan | `23` |
| ⚡ Hysteria2 | `3` |
| **ИТОГО** | **`414`** |

### 📱 LTE

| Протокол | Количество |
|----------|------------|
| 🔗 VLESS | `25` |
| 📦 VMess | `2` |
| 🛡️ Trojan | `0` |
| ⚡ Hysteria2 | `0` |
| **ИТОГО** | **`27`** |

### 📶 WIFI

| Протокол | Количество |
|----------|------------|
| 🔗 VLESS | `327` |
| 📦 VMess | `34` |
| 🛡️ Trojan | `23` |
| ⚡ Hysteria2 | `3` |
| **ИТОГО** | **`387`** |

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
