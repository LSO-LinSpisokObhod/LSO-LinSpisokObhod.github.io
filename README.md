# 🚀 LinSpisokObhod

## 📅 Время последнего сбора

`2026-11-06 10:26:21 (UTC+3)`

---

## 📊 Статистика по файлам

| Файл | Всего конфигов |
|------|----------------|
| 📁 ALL.txt / ALL.yml / ALL.json | `521` |
| 📱 LTE.txt / LTE.yml / LTE.json | `52` |
| 📶 WIFI.txt / WIFI.yml / WIFI.json | `469` |

---

## 📡 Статистика по протоколам

### 🌐 ALL

| Протокол | Количество |
|----------|------------|
| 🔗 VLESS | `395` |
| 📦 VMess | `40` |
| 🛡️ Trojan | `80` |
| ⚡ Hysteria2 | `6` |
| **ИТОГО** | **`521`** |

### 📱 LTE

| Протокол | Количество |
|----------|------------|
| 🔗 VLESS | `44` |
| 📦 VMess | `0` |
| 🛡️ Trojan | `8` |
| ⚡ Hysteria2 | `0` |
| **ИТОГО** | **`52`** |

### 📶 WIFI

| Протокол | Количество |
|----------|------------|
| 🔗 VLESS | `351` |
| 📦 VMess | `40` |
| 🛡️ Trojan | `72` |
| ⚡ Hysteria2 | `6` |
| **ИТОГО** | **`469`** |

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
