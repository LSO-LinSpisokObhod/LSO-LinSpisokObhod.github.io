# 🚀 LinSpisokObhod

## 📅 Время последнего сбора

`2026-11-05 07:02:14 (UTC+3)`

---

## 📊 Статистика по файлам

| Файл | Всего конфигов |
|------|----------------|
| 📁 ALL.txt / ALL.yml / ALL.json | `588` |
| 📱 LTE.txt / LTE.yml / LTE.json | `73` |
| 📶 WIFI.txt / WIFI.yml / WIFI.json | `515` |

---

## 📡 Статистика по протоколам

### 🌐 ALL

| Протокол | Количество |
|----------|------------|
| 🔗 VLESS | `421` |
| 📦 VMess | `44` |
| 🛡️ Trojan | `115` |
| ⚡ Hysteria2 | `8` |
| **ИТОГО** | **`588`** |

### 📱 LTE

| Протокол | Количество |
|----------|------------|
| 🔗 VLESS | `57` |
| 📦 VMess | `1` |
| 🛡️ Trojan | `14` |
| ⚡ Hysteria2 | `1` |
| **ИТОГО** | **`73`** |

### 📶 WIFI

| Протокол | Количество |
|----------|------------|
| 🔗 VLESS | `364` |
| 📦 VMess | `43` |
| 🛡️ Trojan | `101` |
| ⚡ Hysteria2 | `7` |
| **ИТОГО** | **`515`** |

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
