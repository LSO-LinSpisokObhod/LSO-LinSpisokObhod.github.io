# 🚀 LinSpisokObhod

## 📅 Время последнего сбора

`2026-11-06 20:00:37 (UTC+3)`

---

## 📊 Статистика по файлам

| Файл | Всего конфигов |
|------|----------------|
| 📁 ALL.txt / ALL.yml / ALL.json | `364` |
| 📱 LTE.txt / LTE.yml / LTE.json | `33` |
| 📶 WIFI.txt / WIFI.yml / WIFI.json | `331` |

---

## 📡 Статистика по протоколам

### 🌐 ALL

| Протокол | Количество |
|----------|------------|
| 🔗 VLESS | `222` |
| 📦 VMess | `46` |
| 🛡️ Trojan | `93` |
| ⚡ Hysteria2 | `3` |
| **ИТОГО** | **`364`** |

### 📱 LTE

| Протокол | Количество |
|----------|------------|
| 🔗 VLESS | `25` |
| 📦 VMess | `0` |
| 🛡️ Trojan | `8` |
| ⚡ Hysteria2 | `0` |
| **ИТОГО** | **`33`** |

### 📶 WIFI

| Протокол | Количество |
|----------|------------|
| 🔗 VLESS | `197` |
| 📦 VMess | `46` |
| 🛡️ Trojan | `85` |
| ⚡ Hysteria2 | `3` |
| **ИТОГО** | **`331`** |

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
