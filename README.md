# 🚀 LinSpisokObhod

## 📅 Время последнего сбора

`2026-11-10 12:47:38 (UTC+3)`

---

## 📊 Статистика по файлам

| Файл | Всего конфигов |
|------|----------------|
| 📁 ALL.txt / ALL.yml / ALL.json | `162` |
| 📱 LTE.txt / LTE.yml / LTE.json | `8` |
| 📶 WIFI.txt / WIFI.yml / WIFI.json | `154` |

---

## 📡 Статистика по протоколам

### 🌐 ALL

| Протокол | Количество |
|----------|------------|
| 🔗 VLESS | `143` |
| 📦 VMess | `12` |
| 🛡️ Trojan | `7` |
| ⚡ Hysteria2 | `0` |
| **ИТОГО** | **`162`** |

### 📱 LTE

| Протокол | Количество |
|----------|------------|
| 🔗 VLESS | `8` |
| 📦 VMess | `0` |
| 🛡️ Trojan | `0` |
| ⚡ Hysteria2 | `0` |
| **ИТОГО** | **`8`** |

### 📶 WIFI

| Протокол | Количество |
|----------|------------|
| 🔗 VLESS | `135` |
| 📦 VMess | `12` |
| 🛡️ Trojan | `7` |
| ⚡ Hysteria2 | `0` |
| **ИТОГО** | **`154`** |

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
