# 🚀 LinSpisokObhod

## 📅 Время последнего сбора

`2026-11-13 08:15:37 (UTC+3)`

---

## 📊 Статистика по файлам

| Файл | Всего конфигов |
|------|----------------|
| 📁 ALL.txt / ALL.yml / ALL.json | `972` |
| 📱 LTE.txt / LTE.yml / LTE.json | `58` |
| 📶 WIFI.txt / WIFI.yml / WIFI.json | `914` |

---

## 📡 Статистика по протоколам

### 🌐 ALL

| Протокол | Количество |
|----------|------------|
| 🔗 VLESS | `487` |
| 📦 VMess | `29` |
| 🛡️ Trojan | `437` |
| ⚡ Hysteria2 | `19` |
| **ИТОГО** | **`972`** |

### 📱 LTE

| Протокол | Количество |
|----------|------------|
| 🔗 VLESS | `46` |
| 📦 VMess | `1` |
| 🛡️ Trojan | `10` |
| ⚡ Hysteria2 | `1` |
| **ИТОГО** | **`58`** |

### 📶 WIFI

| Протокол | Количество |
|----------|------------|
| 🔗 VLESS | `441` |
| 📦 VMess | `28` |
| 🛡️ Trojan | `427` |
| ⚡ Hysteria2 | `18` |
| **ИТОГО** | **`914`** |

---

## 🗂️ Фильтрация

1. **fp=chrome → fp=firefox** — все конфиги с `fp=chrome` автоматически переписываются на `fp=firefox` (без удаления).
2. **TCP-проверка** — двухпроходная (5s быстрая + 30s медленная).
3. **LTE** — SNI домен есть в `whitelist.txt` **ИЛИ** IP входит в CIDR из `cidrwhitelist.txt`.
4. **WIFI** — все остальные рабочие конфиги.
5. **ALL** — все конфиги из всех источников.

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
