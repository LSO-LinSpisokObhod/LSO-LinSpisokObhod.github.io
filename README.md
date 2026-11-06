# 🚀 LinSpisokObhod

## 📅 Время последнего сбора

`2026-11-06 14:12:01 (UTC+3)`

---

## 📊 Статистика по файлам

| Файл | Всего конфигов |
|------|----------------|
| 📁 ALL.txt / ALL.yml / ALL.json | `366` |
| 📱 LTE.txt / LTE.yml / LTE.json | `18` |
| 📶 WIFI.txt / WIFI.yml / WIFI.json | `348` |

---

## 📡 Статистика по протоколам

### 🌐 ALL

| Протокол | Количество |
|----------|------------|
| 🔗 VLESS | `222` |
| 📦 VMess | `38` |
| 🛡️ Trojan | `101` |
| ⚡ Hysteria2 | `5` |
| **ИТОГО** | **`366`** |

### 📱 LTE

| Протокол | Количество |
|----------|------------|
| 🔗 VLESS | `10` |
| 📦 VMess | `0` |
| 🛡️ Trojan | `8` |
| ⚡ Hysteria2 | `0` |
| **ИТОГО** | **`18`** |

### 📶 WIFI

| Протокол | Количество |
|----------|------------|
| 🔗 VLESS | `212` |
| 📦 VMess | `38` |
| 🛡️ Trojan | `93` |
| ⚡ Hysteria2 | `5` |
| **ИТОГО** | **`348`** |

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
