# 🚀 LinSpisokObhod

## 📅 Время последнего сбора

`2026-11-08 04:27:12 (UTC+3)`

---

## 📊 Статистика по файлам

| Файл | Всего конфигов |
|------|----------------|
| 📁 ALL.txt / ALL.yml / ALL.json | `374` |
| 📱 LTE.txt / LTE.yml / LTE.json | `29` |
| 📶 WIFI.txt / WIFI.yml / WIFI.json | `345` |

---

## 📡 Статистика по протоколам

### 🌐 ALL

| Протокол | Количество |
|----------|------------|
| 🔗 VLESS | `317` |
| 📦 VMess | `38` |
| 🛡️ Trojan | `16` |
| ⚡ Hysteria2 | `3` |
| **ИТОГО** | **`374`** |

### 📱 LTE

| Протокол | Количество |
|----------|------------|
| 🔗 VLESS | `29` |
| 📦 VMess | `0` |
| 🛡️ Trojan | `0` |
| ⚡ Hysteria2 | `0` |
| **ИТОГО** | **`29`** |

### 📶 WIFI

| Протокол | Количество |
|----------|------------|
| 🔗 VLESS | `288` |
| 📦 VMess | `38` |
| 🛡️ Trojan | `16` |
| ⚡ Hysteria2 | `3` |
| **ИТОГО** | **`345`** |

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
