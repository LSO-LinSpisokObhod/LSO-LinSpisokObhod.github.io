# 🚀 LinSpisokObhod

## 📅 Время последнего сбора

`2026-11-05 13:14:35 (UTC+3)`

---

## 📊 Статистика по файлам

| Файл | Всего конфигов |
|------|----------------|
| 📁 ALL.txt / ALL.yml / ALL.json | `490` |
| 📱 LTE.txt / LTE.yml / LTE.json | `53` |
| 📶 WIFI.txt / WIFI.yml / WIFI.json | `437` |

---

## 📡 Статистика по протоколам

### 🌐 ALL

| Протокол | Количество |
|----------|------------|
| 🔗 VLESS | `335` |
| 📦 VMess | `38` |
| 🛡️ Trojan | `109` |
| ⚡ Hysteria2 | `8` |
| **ИТОГО** | **`490`** |

### 📱 LTE

| Протокол | Количество |
|----------|------------|
| 🔗 VLESS | `39` |
| 📦 VMess | `1` |
| 🛡️ Trojan | `13` |
| ⚡ Hysteria2 | `0` |
| **ИТОГО** | **`53`** |

### 📶 WIFI

| Протокол | Количество |
|----------|------------|
| 🔗 VLESS | `296` |
| 📦 VMess | `37` |
| 🛡️ Trojan | `96` |
| ⚡ Hysteria2 | `8` |
| **ИТОГО** | **`437`** |

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
