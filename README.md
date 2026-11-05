# 🚀 LinSpisokObhod

## 📅 Время последнего сбора

`2026-11-05 08:07:54 (UTC+3)`

---

## 📊 Статистика по файлам

| Файл | Всего конфигов |
|------|----------------|
| 📁 ALL.txt / ALL.yml / ALL.json | `593` |
| 📱 LTE.txt / LTE.yml / LTE.json | `72` |
| 📶 WIFI.txt / WIFI.yml / WIFI.json | `521` |

---

## 📡 Статистика по протоколам

### 🌐 ALL

| Протокол | Количество |
|----------|------------|
| 🔗 VLESS | `426` |
| 📦 VMess | `45` |
| 🛡️ Trojan | `115` |
| ⚡ Hysteria2 | `7` |
| **ИТОГО** | **`593`** |

### 📱 LTE

| Протокол | Количество |
|----------|------------|
| 🔗 VLESS | `57` |
| 📦 VMess | `1` |
| 🛡️ Trojan | `14` |
| ⚡ Hysteria2 | `0` |
| **ИТОГО** | **`72`** |

### 📶 WIFI

| Протокол | Количество |
|----------|------------|
| 🔗 VLESS | `369` |
| 📦 VMess | `44` |
| 🛡️ Trojan | `101` |
| ⚡ Hysteria2 | `7` |
| **ИТОГО** | **`521`** |

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
