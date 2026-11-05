# 🚀 LinSpisokObhod

## 📅 Время последнего сбора

`2026-11-05 04:15:09 (UTC+3)`

---

## 📊 Статистика по файлам

| Файл | Всего конфигов |
|------|----------------|
| 📁 ALL.txt / ALL.yml / ALL.json | `553` |
| 📱 LTE.txt / LTE.yml / LTE.json | `67` |
| 📶 WIFI.txt / WIFI.yml / WIFI.json | `486` |

---

## 📡 Статистика по протоколам

### 🌐 ALL

| Протокол | Количество |
|----------|------------|
| 🔗 VLESS | `347` |
| 📦 VMess | `43` |
| 🛡️ Trojan | `103` |
| ⚡ Hysteria2 | `60` |
| **ИТОГО** | **`553`** |

### 📱 LTE

| Протокол | Количество |
|----------|------------|
| 🔗 VLESS | `50` |
| 📦 VMess | `1` |
| 🛡️ Trojan | `13` |
| ⚡ Hysteria2 | `3` |
| **ИТОГО** | **`67`** |

### 📶 WIFI

| Протокол | Количество |
|----------|------------|
| 🔗 VLESS | `297` |
| 📦 VMess | `42` |
| 🛡️ Trojan | `90` |
| ⚡ Hysteria2 | `57` |
| **ИТОГО** | **`486`** |

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
