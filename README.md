# 🚀 LinSpisokObhod

## 📅 Время последнего сбора

`2026-11-05 10:28:26 (UTC+3)`

---

## 📊 Статистика по файлам

| Файл | Всего конфигов |
|------|----------------|
| 📁 ALL.txt / ALL.yml / ALL.json | `525` |
| 📱 LTE.txt / LTE.yml / LTE.json | `66` |
| 📶 WIFI.txt / WIFI.yml / WIFI.json | `459` |

---

## 📡 Статистика по протоколам

### 🌐 ALL

| Протокол | Количество |
|----------|------------|
| 🔗 VLESS | `364` |
| 📦 VMess | `43` |
| 🛡️ Trojan | `111` |
| ⚡ Hysteria2 | `7` |
| **ИТОГО** | **`525`** |

### 📱 LTE

| Протокол | Количество |
|----------|------------|
| 🔗 VLESS | `51` |
| 📦 VMess | `1` |
| 🛡️ Trojan | `14` |
| ⚡ Hysteria2 | `0` |
| **ИТОГО** | **`66`** |

### 📶 WIFI

| Протокол | Количество |
|----------|------------|
| 🔗 VLESS | `313` |
| 📦 VMess | `42` |
| 🛡️ Trojan | `97` |
| ⚡ Hysteria2 | `7` |
| **ИТОГО** | **`459`** |

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
