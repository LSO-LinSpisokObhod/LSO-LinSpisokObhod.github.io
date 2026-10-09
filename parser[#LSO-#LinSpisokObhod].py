#!/usr/bin/env python3

import os
import re
import json
import time
import logging
import ipaddress
import shutil
import asyncio
import aiohttp
import base64
import socket
from datetime import datetime, timezone, timedelta
from urllib.parse import parse_qs, quote
from typing import Dict, Set, Optional, List, Tuple

# ========== НАСТРОЙКИ ==========
GEOIP_PARALLEL = 10
GEOIP_DELAY = 0.1

# Токены IPinfo берутся ТОЛЬКО из переменной окружения.
# Можно передать несколько через запятую: IPINFO_TOKEN=tok1,tok2
IPINFO_TOKENS = [
    t.strip() for t in os.environ.get("IPINFO_TOKEN", "").split(",") if t.strip()
]
if not IPINFO_TOKENS:
    raise ValueError("No IPINFO_TOKEN provided. Set env var IPINFO_TOKEN (comma-separated for multiple).")

GEOIP_CACHE = {}
GEOIP_SEMAPHORE = asyncio.Semaphore(GEOIP_PARALLEL)
TOKEN_INDEX = 0
TOKEN_LOCK = asyncio.Lock()

REQUEST_TIMEOUT = 15
CONFIG_DIR = "sub"
LISTS_DIR = "lists"
WHITELIST_FILE = os.path.join(LISTS_DIR, "whitelist.txt")
CIDR_WHITELIST_FILE = os.path.join(LISTS_DIR, "cidrwhitelist.txt")
GLOBAL_TAG = "[#LSO - #LinSpisokObhod]"
ESPD_TAG = "[#LOESPD - #LinSpisokObhod]"

PROTOCOL_PATTERNS = {
    'vless':     re.compile(r'vless://[A-Za-z0-9+/=@:;,\?&%#\.\-_~!$*()]+', re.IGNORECASE),
    # vmess: base64 может содержать '+', '/', '=', а после — '#comment'.
    # Берём всё до whitespace/кавычек/угловых скобок, чтобы не обрезать хвост.
    'vmess':     re.compile(r'vmess://[^\s"\'`<>]+', re.IGNORECASE),
    'trojan':    re.compile(r'trojan://[A-Za-z0-9+/=@:;,\?&%#\.\-_~!$*()]+', re.IGNORECASE),
    'hysteria2': re.compile(r'(?:hysteria2|hy2)://[A-Za-z0-9+/=@:;,\?&%#\.\-_~!$*()]+', re.IGNORECASE),
}

# Алиасы протоколов: 'hy2://' и 'hysteria2://' → 'hysteria2'
PROTOCOL_PREFIXES = {
    'vless': ('vless',),
    'vmess': ('vmess',),
    'trojan': ('trojan',),
    'hysteria2': ('hysteria2', 'hy2'),
}


def detect_protocol(config: str) -> Optional[str]:
    """Возвращает канонический ключ протокола ('hysteria2' для hy2:// и hysteria2://) или None."""
    for proto, prefixes in PROTOCOL_PREFIXES.items():
        for prefix in prefixes:
            if config.startswith(prefix + "://"):
                return proto
    return None


def strip_protocol(config: str) -> str:
    """Убирает 'proto://' (учитывая алиасы 'hy2')."""
    for proto, prefixes in PROTOCOL_PREFIXES.items():
        for prefix in prefixes:
            if config.startswith(prefix + "://"):
                return config[len(prefix) + 3:]
    return config


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# === ЗАГРУЗКА ИСТОЧНИКОВ ИЗ ФАЙЛА ===
def load_sources_from_file(path: str = "source.txt") -> List[str]:
    sources = []
    if not os.path.exists(path):
        logger.error(f"❌ Файл {path} не найден! Создайте его с URL-адресами подписок.")
        return sources
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                sources.append(line)
    return sources


# === TCP-ПРОВЕРКА (ТАЙМАУТ 30 СЕКУНД) ===
async def check_tcp_port(host: str, port: int, timeout: float = 30.0) -> bool:
    try:
        loop = asyncio.get_running_loop()
        try:
            await asyncio.wait_for(
                loop.create_connection(lambda: asyncio.Protocol(), host, port),
                timeout=timeout
            )
            return True
        except (ConnectionRefusedError, TimeoutError, OSError, socket.gaierror, asyncio.TimeoutError):
            return False
        except Exception:
            return False
    except Exception:
        return False


# === ДЕКОДИРОВАНИЕ BASE64 ===
def decode_base64_if_needed(content: str) -> str:
    content = content.strip()
    if len(content) < 20:
        return content
    if not re.match(r'^[A-Za-z0-9+/]*={0,2}$', content):
        return content
    try:
        decoded_bytes = base64.b64decode(content, validate=True)
        decoded_str = decoded_bytes.decode('utf-8', errors='ignore')
        if '://' in decoded_str:
            return decoded_str
        if decoded_str.isprintable() and len(decoded_str) > 50:
            return decoded_str
    except Exception:
        pass
    return content


# === АСИНХРОННАЯ ЗАГРУЗКА ===
async def fetch_url_content(session: aiohttp.ClientSession, url: str) -> Optional[str]:
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        async with session.get(url, timeout=REQUEST_TIMEOUT, headers=headers) as response:
            if response.status == 200:
                content = await response.text()
                content = decode_base64_if_needed(content)
                logger.info(f"📦 {url} -> длина {len(content)}, начало: {content[:200]}")
                return content
            else:
                logger.warning(f"⚠️ Ошибка {response.status} при загрузке {url}")
    except Exception as e:
        logger.warning(f"⚠️ Ошибка загрузки {url}: {e}")
    return None


async def fetch_all_sources(sources: List[str]):
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_url_content(session, url) for url in sources]
        results = await asyncio.gather(*tasks)
    return dict(zip(sources, results))


# === ПАРСИНГ КОНФИГОВ ===
def extract_configs_from_text(text: str) -> Dict[str, Set[str]]:
    configs = {proto: set() for proto in PROTOCOL_PATTERNS}
    for protocol, pattern in PROTOCOL_PATTERNS.items():
        for match in pattern.findall(text):
            if 50 < len(match) < 5000:
                configs[protocol].add(match)
    if not any(configs.values()):
        for token in re.split(r'[\s,]+', text):
            token = token.strip()
            if not token:
                continue
            for protocol, pattern in PROTOCOL_PATTERNS.items():
                if pattern.match(token) and 50 < len(token) < 5000:
                    configs[protocol].add(token)
    return configs


# === VMESS: НАДЁЖНЫЙ ДЕКОДЕР ===
def _vmess_b64_normalize(s: str) -> str:
    """Приводит base64 к стандартному виду: URL-safe → стандарт, добавляет padding."""
    s = s.strip().replace('-', '+').replace('_', '/')
    # Убираем всё, что не из base64-алфавита (пробелы, переносы, случайные символы)
    s = re.sub(r'[^A-Za-z0-9+/=]', '', s)
    pad = (-len(s)) % 4
    if pad:
        s += '=' * pad
    return s


def decode_vmess_config(config: str) -> Optional[Dict]:
    """Возвращает JSON-словарь vmess-конфига или None.

    Устойчив к:
      - '#'-комментарию после base64;
      - '?query' после base64 (некоторые панели добавляют remarks);
      - отсутствию padding;
      - URL-safe алфавиту;
      - пробелам/переносам внутри base64.
    """
    if not config.startswith('vmess://'):
        return None
    payload = config[8:]

    # Отрезаем '#comment' и '?query' — они не часть base64
    payload = payload.split('#', 1)[0]
    payload = payload.split('?', 1)[0].strip()

    if not payload:
        return None

    try:
        decoded = base64.b64decode(
            _vmess_b64_normalize(payload), validate=False
        ).decode('utf-8', errors='ignore')
    except Exception:
        return None

    try:
        data = json.loads(decoded)
    except Exception:
        return None

    if not isinstance(data, dict):
        return None

    # Обязательное поле: 'add' (адрес сервера)
    add = data.get('add')
    if not isinstance(add, str) or not add.strip():
        return None

    return data


def _vmess_host(data: Dict) -> Optional[str]:
    """host/ip из vmess-JSON, включая корректную обработку IPv6."""
    host = data.get('add')
    if not isinstance(host, str):
        return None
    host = host.strip().strip('[]')       # [::1] → ::1
    return host or None


def _vmess_port(data: Dict, default: int = 443) -> int:
    """Порт из vmess-JSON; поле 'port' может быть строкой или числом."""
    raw = data.get('port')
    try:
        port = int(raw)
        if 1 <= port <= 65535:
            return port
    except (TypeError, ValueError):
        pass
    return default


def _vmess_sni(data: Dict) -> Optional[str]:
    """SNI из vmess-JSON: 'sni' → 'host' → None (НЕ 'add'!)."""
    for key in ('sni', 'host'):
        v = data.get(key)
        if isinstance(v, str) and v.strip():
            return v.strip()
    return None


def _vmess_transport(data: Dict) -> str:
    """Транспорт из vmess-JSON поля 'net'."""
    net = (data.get('net') or '').lower().strip()
    if net == 'ws':     return 'WebSocket'
    if net == 'grpc':   return 'GRPC'
    if net == 'h2':     return 'HTTP2'
    if net == 'quic':   return 'QUIC'
    if net == 'kcp':    return 'KCP'
    if net == 'tcp':    return 'TCP'
    return net.upper() if net else 'unknown'


# === ИЗВЛЕЧЕНИЕ HOST / IP / SNI ===
def extract_host_from_config(config: str) -> Optional[str]:
    protocol = detect_protocol(config)
    if not protocol:
        return None

    # VMess: host в base64-JSON поле 'add'
    if protocol == 'vmess':
        data = decode_vmess_config(config)
        return _vmess_host(data) if data else None

    body = strip_protocol(config)
    if '@' not in body:
        return None
    host_part = body.split('@', 1)[1]

    # IPv6: [2001:db8::1]:443
    if host_part.startswith('['):
        return host_part[1:].split(']', 1)[0]

    host = host_part.split(':', 1)[0]
    host = host.split('/', 1)[0].split('?', 1)[0].split('#', 1)[0]
    return host or None


def extract_ip_from_config(config: str) -> Optional[str]:
    host = extract_host_from_config(config)
    if host:
        try:
            ipaddress.ip_address(host)
            return host
        except ValueError:
            return None
    return None


def extract_sni_domain(config: str) -> Optional[str]:
    protocol = detect_protocol(config)
    if not protocol:
        return None

    if protocol == 'vmess':
        data = decode_vmess_config(config)
        return _vmess_sni(data) if data else None

    body = strip_protocol(config)
    if '?' in body:
        query_part = body.split('?', 1)[1].split('#', 1)[0]
        params = parse_qs(query_part)
        if 'sni' in params:
            return params['sni'][0]
        if 'host' in params:
            return params['host'][0]
    return None


def get_endpoint(cfg: str) -> Optional[Tuple[str, int]]:
    """Возвращает (host, port) для TCP-теста. Работает для всех протоколов, включая vmess."""
    protocol = detect_protocol(cfg)
    if not protocol:
        return None

    if protocol == 'vmess':
        data = decode_vmess_config(cfg)
        if not data:
            return None
        host = _vmess_host(data)
        if not host:
            return None
        return host, _vmess_port(data, 443)

    # vless / trojan / hysteria2 — user@host:port
    host = extract_host_from_config(cfg)
    if not host:
        return None
    port = 443
    m = re.search(r'@[^:]+:(\d+)', cfg)
    if m:
        port = int(m.group(1))
    else:
        m = re.search(r'[?&]port=(\d+)', cfg)
        if m:
            port = int(m.group(1))
    return host, port


# === ДЕДУБЛИКАЦИЯ ===
def get_config_key(config: str) -> str:
    """Ключ для дедубликации: всё, что стоит до символа # (буква в букву)."""
    return config.split('#')[0].strip()


def deduplicate_configs(configs: List[str]) -> List[str]:
    seen_keys = set()
    unique_configs = []
    duplicates_count = 0

    for cfg in configs:
        key = get_config_key(cfg)
        if key not in seen_keys:
            seen_keys.add(key)
            unique_configs.append(cfg)
        else:
            duplicates_count += 1

    if duplicates_count > 0:
        logger.info(f"🔁 Удалено дубликатов: {duplicates_count} (осталось {len(unique_configs)})")

    return unique_configs


# === ГЕОЛОКАЦИЯ (IPinfo с ротацией токенов) ===
async def get_next_token() -> str:
    global TOKEN_INDEX
    async with TOKEN_LOCK:
        token = IPINFO_TOKENS[TOKEN_INDEX % len(IPINFO_TOKENS)]
        TOKEN_INDEX += 1
        return token


async def resolve_country(ip: str, session: aiohttp.ClientSession, attempt: int = 0) -> str:
    if attempt >= max(len(IPINFO_TOKENS), 1) * 2:
        GEOIP_CACHE[ip] = 'XX'
        return 'XX'

    async with GEOIP_SEMAPHORE:
        if ip in GEOIP_CACHE:
            return GEOIP_CACHE[ip]
        token = await get_next_token()
        country = 'XX'
        try:
            url = f"https://api.ipinfo.io/lite/{ip}/country?token={token}"
            async with session.get(url, timeout=5) as resp:
                if resp.status == 200:
                    country = (await resp.text()).strip() or 'XX'
                    if len(GEOIP_CACHE) < 5 and country != 'XX':
                        logger.info(f"✅ IPinfo (token {token[:4]}...): {ip} -> {country}")
                elif resp.status == 429:
                    logger.warning(f"⚠️ Токен {token[:4]}... лимит, переключаюсь")
                    return await resolve_country(ip, session, attempt + 1)
                else:
                    logger.debug(f"⚠️ IPinfo ошибка {resp.status} для {ip}")
        except Exception as e:
            logger.debug(f"Ошибка IPinfo для {ip}: {e}")
        GEOIP_CACHE[ip] = country
        return country


async def resolve_countries_parallel(ips: List[str]) -> Dict[str, str]:
    if not ips:
        return {}
    unique_ips = [ip for ip in set(ips) if ip not in GEOIP_CACHE]
    if not unique_ips:
        return GEOIP_CACHE.copy()
    total = len(unique_ips)
    logger.info(f"🌍 Определяю страны для {total} уникальных IP через IPinfo (параллельно {GEOIP_PARALLEL})")
    processed = 0
    async with aiohttp.ClientSession() as session:
        tasks = [resolve_country(ip, session) for ip in unique_ips]
        for future in asyncio.as_completed(tasks):
            await future
            processed += 1
            if processed % 100 == 0 or processed == total:
                logger.info(f"   Прогресс геолокации: {processed}/{total} IP обработано")
            await asyncio.sleep(GEOIP_DELAY)
    logger.info("✅ Геолокация завершена")
    return GEOIP_CACHE.copy()


# === ПЕРЕИМЕНОВАНИЕ КОНФИГОВ (URL-encoded) ===
def rename_config(config: str, country: str = '', tag: str = GLOBAL_TAG) -> str:
    protocol = detect_protocol(config)
    if not protocol:
        return config

    if '#' in config:
        config = config.rsplit('#', 1)[0].rstrip()

    sni = extract_sni_domain(config)
    host = extract_host_from_config(config)
    ip = extract_ip_from_config(config)

    conn_type = "unknown"
    if protocol == 'vmess':
        data = decode_vmess_config(config)
        if data:
            conn_type = _vmess_transport(data)
    else:
        body = strip_protocol(config)
        if '?' in body:
            query_part = body.split('?', 1)[1].split('#', 1)[0]
            params = parse_qs(query_part)
            if 'type' in params:
                t = params['type'][0].lower()
                conn_type = "WebSocket" if t == 'ws' else t.upper()
    if protocol == 'hysteria2':
        conn_type = "HYSTERIA2"

    parts = [
        country if (ip and country and country != 'XX') else "unknown",
        sni or host or "unknown",
        conn_type,
        tag,
    ]
    return config + "#" + quote(" | ".join(parts), safe='')


# === БЕЛЫЕ СПИСКИ ===
def ensure_lists_dir():
    if not os.path.exists(LISTS_DIR):
        os.makedirs(LISTS_DIR)


def load_whitelist() -> Set[str]:
    ensure_lists_dir()
    whitelist = set()
    if not os.path.exists(WHITELIST_FILE):
        with open(WHITELIST_FILE, 'w', encoding='utf-8') as f:
            f.write("# Домены/зоны для LTE (приоритет 1)\n")
            f.write("# Формат:\n")
            f.write("#   example.com    — домен и его субдомены\n")
            f.write("#   .example.com   — только субдомены example.com\n")
            f.write("#   .yandex        — любой домен, содержащий лейбл 'yandex' (yandex.ru, mail.yandex.ru, yandex.com, ...)\n")
            f.write("example.com\n")
            f.write(".yandex\n")
        logger.info(f"📝 Создан пример {WHITELIST_FILE}")
        return whitelist
    with open(WHITELIST_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                whitelist.add(line)
    logger.info(f"📋 Загружено {len(whitelist)} доменов/зон")
    return whitelist


def load_cidr_whitelist() -> List[ipaddress.ip_network]:
    ensure_lists_dir()
    cidr_list = []
    if not os.path.exists(CIDR_WHITELIST_FILE):
        with open(CIDR_WHITELIST_FILE, 'w', encoding='utf-8') as f:
            f.write("# CIDR сети для LTE (приоритет 2)\n")
            f.write("1.1.1.0/24\n")
            f.write("2.2.2.2/32\n")
            f.write("192.168.0.0/16\n")
        logger.info(f"📝 Создан пример {CIDR_WHITELIST_FILE}")
        return cidr_list
    with open(CIDR_WHITELIST_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                try:
                    cidr_list.append(ipaddress.ip_network(line, strict=False))
                except ValueError:
                    logger.warning(f"⚠️ Некорректная CIDR: {line}")
    logger.info(f"📋 Загружено {len(cidr_list)} CIDR сетей")
    return cidr_list


def is_ip_in_cidr_list(ip_str: str, cidr_list: List[ipaddress.ip_network]) -> bool:
    if not ip_str or not cidr_list:
        return False
    try:
        ip = ipaddress.ip_address(ip_str)
        return any(ip in net for net in cidr_list)
    except ValueError:
        return False


def is_domain_allowed(domain: str, whitelist: Set[str]) -> bool:
    if not domain:
        return False
    domain = domain.lower()
    domain_labels = domain.split('.')
    for allowed in whitelist:
        a = allowed.lower()
        if a.startswith('.'):
            tail = a[1:]
            if '.' in tail:
                # '.example.com' — субдомены example.com, сам example.com не матчится
                if domain.endswith(a):
                    return True
            else:
                # '.yandex' — любой домен с лейблом 'yandex'
                if tail in domain_labels:
                    return True
        else:
            if domain == a or domain.endswith('.' + a):
                return True
    return False


def get_config_priority(config: str, whitelist: Set[str], cidr_list: List[ipaddress.ip_network]) -> int:
    sni = extract_sni_domain(config)
    if sni and is_domain_allowed(sni, whitelist):
        return 0
    ip = extract_ip_from_config(config)
    if ip and is_ip_in_cidr_list(ip, cidr_list):
        return 1
    return 2


def count_protocols(configs) -> Dict[str, int]:
    counts = {p: 0 for p in PROTOCOL_PATTERNS}
    for cfg in configs:
        proto = detect_protocol(cfg)
        if proto:
            counts[proto] += 1
    return counts


# === ОСНОВНОЙ СБОР С TCP-ТЕСТИРОВАНИЕМ ===
async def collect_configs_async(contents: Dict[str, Optional[str]]) -> Dict[str, Tuple[str, str]]:
    """
    Возвращает dict: {renamed_config: (original_config, country)}.
    """
    raw_configs: List[str] = []
    all_ips: Set[str] = set()

    for url, content in contents.items():
        if not content:
            continue
        configs_by_proto = extract_configs_from_text(content)
        for protocol, config_set in configs_by_proto.items():
            if not config_set:
                continue
            logger.info(f"📥 +{len(config_set)} {protocol.upper()} из {url}")
            for cfg in config_set:
                raw_configs.append(cfg)
                ip = extract_ip_from_config(cfg)
                if ip:
                    all_ips.add(ip)

    total_raw = len(raw_configs)
    logger.info(f"🔄 Всего конфигов (до дедубликации): {total_raw}")

    raw_configs = deduplicate_configs(raw_configs)
    logger.info(f"🔄 После дедубликации: {len(raw_configs)}")

    # ---- TCP-ТЕСТИРОВАНИЕ ----
    if raw_configs:
        logger.info(f"🔍 Начинаю TCP-тестирование {len(raw_configs)} конфигов (таймаут 30 сек)...")
        unique_endpoints: Set[Tuple[str, int]] = set()
        for cfg in raw_configs:
            ep = get_endpoint(cfg)
            if ep:
                unique_endpoints.add(ep)

        if unique_endpoints:
            total_endpoints = len(unique_endpoints)
            logger.info(f"🌐 Уникальных эндпоинтов для проверки: {total_endpoints}")
            sem = asyncio.Semaphore(20)
            checked_count = 0

            async def check_endpoint(host, port):
                nonlocal checked_count
                async with sem:
                    result = host, port, await check_tcp_port(host, port)
                    checked_count += 1
                    if checked_count % 100 == 0 or checked_count == total_endpoints:
                        logger.info(f"⏳ Прогресс TCP-тестирования: {checked_count}/{total_endpoints} эндпоинтов проверено")
                    return result

            tasks = [check_endpoint(host, port) for (host, port) in unique_endpoints]
            results = await asyncio.gather(*tasks)
            alive_endpoints = {(h, p) for h, p, alive in results if alive}
            logger.info(f"✅ Рабочих эндпоинтов: {len(alive_endpoints)}")

            filtered_configs: List[str] = []
            for cfg in raw_configs:
                ep = get_endpoint(cfg)
                if ep and ep in alive_endpoints:
                    filtered_configs.append(cfg)

            raw_configs = filtered_configs
            logger.info(f"✅ После TCP-тестирования осталось {len(raw_configs)} конфигов")
        else:
            logger.info("⚠️ Не найдено эндпоинтов для TCP-тестирования")

    # ---- ГЕОЛОКАЦИЯ ----
    if all_ips:
        await resolve_countries_parallel(list(all_ips))
    else:
        logger.info("🌍 Геолокация: IP для определения не найдены")

    # ---- ПЕРЕИМЕНОВАНИЕ ----
    configs_map: Dict[str, Tuple[str, str]] = {}
    for i, cfg in enumerate(raw_configs, 1):
        ip = extract_ip_from_config(cfg)
        country = GEOIP_CACHE.get(ip, '') if ip else ''
        renamed_cfg = rename_config(cfg, country, tag=GLOBAL_TAG)
        if renamed_cfg not in configs_map:
            configs_map[renamed_cfg] = (cfg, country)
        if i % 500 == 0 or i == len(raw_configs):
            logger.info(f"⏳ Прогресс переименования: {i}/{len(raw_configs)} конфигов")

    logger.info(f"📊 Собрано уникальных конфигов: {len(configs_map)}")
    return configs_map


# === README.md ===
def update_readme(total: int, lte: int, wifi: int, espd: int,
                 protocols_all: Dict[str, int],
                 protocols_lte: Dict[str, int],
                 protocols_wifi: Dict[str, int],
                 protocols_espd: Dict[str, int]):
    moscow_time = get_moscow_time()

    readme_content = f"""# 🚀 LinSpisokObhod

## 📅 Время последнего сбора

`{moscow_time} (UTC+3)`

---

## 📊 Статистика по файлам

| Файл | Всего конфигов |
|------|----------------|
| 📁 ALL.txt / ALL.64.txt | `{total}` |
| 📱 LTE.txt / LTE.64.txt | `{lte}` |
| 📶 WIFI.txt / WIFI.64.txt | `{wifi}` |
| 🏫 LinObhodESPD.txt / LinObhodESPD.64.txt | `{espd}` |

---

## 📡 Статистика по протоколам

### 🌐 ALL.txt

| Протокол | Количество |
|----------|------------|
| 🔗 VLESS | `{protocols_all.get('vless', 0)}` |
| 📦 VMess | `{protocols_all.get('vmess', 0)}` |
| 🛡️ Trojan | `{protocols_all.get('trojan', 0)}` |
| ⚡ Hysteria2 | `{protocols_all.get('hysteria2', 0)}` |
| **ИТОГО** | **`{total}`** |

### 📱 LTE.txt

| Протокол | Количество |
|----------|------------|
| 🔗 VLESS | `{protocols_lte.get('vless', 0)}` |
| 📦 VMess | `{protocols_lte.get('vmess', 0)}` |
| 🛡️ Trojan | `{protocols_lte.get('trojan', 0)}` |
| ⚡ Hysteria2 | `{protocols_lte.get('hysteria2', 0)}` |
| **ИТОГО** | **`{lte}`** |

### 📶 WIFI.txt

| Протокол | Количество |
|----------|------------|
| 🔗 VLESS | `{protocols_wifi.get('vless', 0)}` |
| 📦 VMess | `{protocols_wifi.get('vmess', 0)}` |
| 🛡️ Trojan | `{protocols_wifi.get('trojan', 0)}` |
| ⚡ Hysteria2 | `{protocols_wifi.get('hysteria2', 0)}` |
| **ИТОГО** | **`{wifi}`** |

### 🏫 LinObhodESPD.txt

| Протокол | Количество |
|----------|------------|
| 🔗 VLESS | `{protocols_espd.get('vless', 0)}` |
| 📦 VMess | `{protocols_espd.get('vmess', 0)}` |
| 🛡️ Trojan | `{protocols_espd.get('trojan', 0)}` |
| ⚡ Hysteria2 | `{protocols_espd.get('hysteria2', 0)}` |
| **ИТОГО** | **`{espd}`** |

---

## 📋 Сводная таблица

| Протокол | ALL | LTE | WIFI | ESPD |
|----------|-----|-----|------|------|
| 🔗 VLESS | `{protocols_all.get('vless', 0)}` | `{protocols_lte.get('vless', 0)}` | `{protocols_wifi.get('vless', 0)}` | `{protocols_espd.get('vless', 0)}` |
| 📦 VMess | `{protocols_all.get('vmess', 0)}` | `{protocols_lte.get('vmess', 0)}` | `{protocols_wifi.get('vmess', 0)}` | `{protocols_espd.get('vmess', 0)}` |
| 🛡️ Trojan | `{protocols_all.get('trojan', 0)}` | `{protocols_lte.get('trojan', 0)}` | `{protocols_wifi.get('trojan', 0)}` | `{protocols_espd.get('trojan', 0)}` |
| ⚡ Hysteria2 | `{protocols_all.get('hysteria2', 0)}` | `{protocols_lte.get('hysteria2', 0)}` | `{protocols_wifi.get('hysteria2', 0)}` | `{protocols_espd.get('hysteria2', 0)}` |

---

## 🗂️ Логика фильтрации

1. **LTE** — SNI домен есть в `whitelist.txt` **ИЛИ** IP входит в CIDR из `cidrwhitelist.txt`.
2. **WIFI** — все остальные рабочие конфиги.
3. **LinObhodESPD** — конфиги с SNI `max.ru` или `api-maps.yandex.ru`.
4. **ALL** — все конфиги из всех источников.

---

## 📁 Доступные файлы

- `sub/ALL.txt` — все конфиги
- `sub/LTE.txt` — для мобильного интернета
- `sub/WIFI.txt` — для Wi-Fi сетей
- `sub/LinObhodESPD.txt` — для ЭСПД
- `sub/*.64.txt` — те же файлы в base64

---

## 🔄 Автообновление

Скрипт запускается **каждый час**.

---

*LinSpisokObhod v3.10*
"""
    with open("README.md", 'w', encoding='utf-8') as f:
        f.write(readme_content)
    logger.info("📄 README.md обновлён (со статистикой по файлам и протоколам)")


def get_moscow_time() -> str:
    moscow_tz = timezone(timedelta(hours=3))
    now_msk = datetime.now(moscow_tz)
    return now_msk.strftime("%Y-%m-%d %H:%M:%S")


# === ГЕНЕРАЦИЯ СТРОК-ЗАГЛУШЕК ===
def generate_extra_lines(total: int, protocols: Dict[str, int], update_time: str, sub_type: str = "ALL") -> List[str]:
    lines = []

    comment = f"подписка #LSO© обновлена {update_time} {GLOBAL_TAG}"
    lines.append(f"vless://update@update.lso:443?security=tls&encryption=none&insecure=0&headerType=none&type=tcp&allowInsecure=0&sni=update.lso#{quote(comment, safe='')}")

    if sub_type == "LTE":
        comment = f"подписка #LSO© ЭТО: подписка с конфигами для LTE {GLOBAL_TAG}"
    elif sub_type == "WIFI":
        comment = f"подписка #LSO© ЭТО: подписка с конфигами для WIFI {GLOBAL_TAG}"
    else:
        comment = f"подписка #LSO© ЭТО: подписка с конфигами для WIFI и LTE {GLOBAL_TAG}"
    lines.append(f"vless://about@1.about.lso:443?security=tls&encryption=none&insecure=0&headerType=none&type=tcp&allowInsecure=0&sni=about.lso#{quote(comment, safe='')}")

    comment = f"и обхода блокировок РКН {GLOBAL_TAG}"
    lines.append(f"vless://about2@2.about.lso:443?security=none&encryption=none&headerType=none&type=tcp#{quote(comment, safe='')}")

    comment = f"Подписка #LSO© Всего конфигов: {total} {GLOBAL_TAG}"
    lines.append(f"vless://all@all.lso:443?security=tls&encryption=none&insecure=0&headerType=none&type=tcp&allowInsecure=0&sni=all.lso#{quote(comment, safe='')}")

    comment = f"Подписка #LSO© Vless: {protocols.get('vless', 0)} {GLOBAL_TAG}"
    lines.append(f"vless://vless@vless.about.lso:443?security=tls&encryption=none&insecure=0&headerType=none&type=tcp&allowInsecure=0&sni=vless.about.lso#{quote(comment, safe='')}")

    comment = f"Подписка #LSO© Trojan: {protocols.get('trojan', 0)} {GLOBAL_TAG}"
    lines.append(f"trojan://trojan@trojan.about.lso:443?security=tls&insecure=0&headerType=none&type=tcp&allowInsecure=0&sni=trojan.lso#{quote(comment, safe='')}")

    comment = f"Подписка #LSO© Hy2: {protocols.get('hysteria2', 0)} {GLOBAL_TAG}"
    lines.append(f"hysteria2://hy2@hy2.about.lso:443?security=tls&obfs=salamander&obfs-password=hy2&insecure=0&mport=67%2C1488%2C69%2C52%2C42%2C1337%2C228%2C25&sni=hy2.lso#{quote(comment, safe='')}")

    comment = f"Подписка #LSO© Vmess: {protocols.get('vmess', 0)} {GLOBAL_TAG}"
    lines.append(f"vless://vmess@vmess.about.lso:443?security=tls&encryption=none&insecure=0&headerType=none&type=tcp&allowInsecure=0&sni=vmess.about.lso#{quote(comment, safe='')}")

    comment = f"Подписка #LSO© ТГ КАНАЛ: @LSOVPN {GLOBAL_TAG}"
    lines.append(f"vless://tg@tg.lso:443?encryption=none&security=tls&sni=tg.lso&type=tcp&headerType=none#{quote(comment, safe='')}")

    comment = f"ТЕХПОДДЕРЖКА #LSO©: t.me/Kepochka_Miside {GLOBAL_TAG}"
    lines.append(f"vless://support@support.lso:443?security=tls&encryption=none&insecure=0&headerType=none&type=tcp&allowInsecure=0&sni=support.lso#{quote(comment, safe='')}")

    return lines


def generate_espd_lines(total: int, protocols: Dict[str, int], update_time: str) -> List[str]:
    lines = []

    comment = f"подписка #LOESPD© обновлена {update_time} {ESPD_TAG}"
    lines.append(f"vless://update@update.lso:443?security=tls&encryption=none&insecure=0&headerType=none&type=tcp&allowInsecure=0&sni=update.lso#{quote(comment, safe='')}")

    comment = f"подписка #LOESPD© ЭТО: подписка с конфигами для ESPD {ESPD_TAG}"
    lines.append(f"vless://about@1.about.lso:443?security=tls&encryption=none&insecure=0&headerType=none&type=tcp&allowInsecure=0&sni=about.lso#{quote(comment, safe='')}")

    comment = f"Подписка #LOESPD© Всего конфигов: {total} {ESPD_TAG}"
    lines.append(f"vless://all@all.lso:443?security=tls&encryption=none&insecure=0&headerType=none&type=tcp&allowInsecure=0&sni=all.lso#{quote(comment, safe='')}")

    comment = f"Подписка #LOESPD© Vless: {protocols.get('vless', 0)} {ESPD_TAG}"
    lines.append(f"vless://vless@vless.about.lso:443?security=tls&encryption=none&insecure=0&headerType=none&type=tcp&allowInsecure=0&sni=vless.about.lso#{quote(comment, safe='')}")

    comment = f"Подписка #LOESPD© Trojan: {protocols.get('trojan', 0)} {ESPD_TAG}"
    lines.append(f"trojan://trojan@trojan.about.lso:443?security=tls&insecure=0&headerType=none&type=tcp&allowInsecure=0&sni=trojan.lso#{quote(comment, safe='')}")

    comment = f"Подписка #LOESPD© Hy2: {protocols.get('hysteria2', 0)} {ESPD_TAG}"
    lines.append(f"hysteria2://hy2@hy2.about.lso:443?security=tls&obfs=salamander&obfs-password=hy2&insecure=0&mport=67%2C1488%2C69%2C52%2C42%2C1337%2C228%2C25&sni=hy2.lso#{quote(comment, safe='')}")

    comment = f"Подписка #LOESPD© Vmess: {protocols.get('vmess', 0)} {ESPD_TAG}"
    lines.append(f"vless://vmess@vmess.about.lso:443?security=tls&encryption=none&insecure=0&headerType=none&type=tcp&allowInsecure=0&sni=vmess.about.lso#{quote(comment, safe='')}")

    return lines


# === СОХРАНЕНИЕ ===
def save_configs(configs_map: Dict[str, Tuple[str, str]]):
    if os.path.exists(CONFIG_DIR):
        shutil.rmtree(CONFIG_DIR)
        logger.info(f"🗑️ Папка {CONFIG_DIR} удалена (старые файлы очищены)")
    os.makedirs(CONFIG_DIR, exist_ok=True)
    logger.info(f"📁 Папка {CONFIG_DIR} создана заново")

    update_time = get_moscow_time()
    tagged_set: Set[str] = set(configs_map.keys())

    # ---- ESPD (пере-переименование оригиналов под ESPD_TAG) ----
    espd_configs: Set[str] = set()
    for renamed_cfg, (orig_cfg, country) in configs_map.items():
        sni = extract_sni_domain(orig_cfg)
        if sni and ('max.ru' in sni or 'api-maps.yandex.ru' in sni):
            espd_configs.add(rename_config(orig_cfg, country, tag=ESPD_TAG))

    protocol_counts_espd = count_protocols(espd_configs)

    # ---- ЗАГОЛОВКИ ----
    header_all = """#profile-title: #LSO© ALL
#profile-update-interval: 1
#support-url: https://t.me/LSOVPN
#announce: #LSO© ALL
#subscription-userinfo: upload=0; download=0; total=0; expire=0

"""
    header_lte = """#profile-title: #LSO© LTE
#profile-update-interval: 1
#support-url: https://t.me/LSOVPN
#announce: #LSO© LTE
#subscription-userinfo: upload=0; download=0; total=0; expire=0

"""
    header_wifi = """#profile-title: #LSO© WIFI
#profile-update-interval: 1
#support-url: https://t.me/LSOVPN
#announce: #LSO© WIFI
#subscription-userinfo: upload=0; download=0; total=0; expire=0

"""
    header_espd = """#profile-title: 🏫 #LinObhodESPD© 
#profile-update-interval: 1
#support-url: https://t.me/LSOVPN
#announce: #LinObhodESPD©
#subscription-userinfo: upload=0; download=0; total=0; expire=0

"""

    # ---- ALL ----
    protocol_counts_all = count_protocols(tagged_set)
    all_extra = generate_extra_lines(len(tagged_set), protocol_counts_all, update_time, "ALL")
    all_path = os.path.join(CONFIG_DIR, "ALL.txt")
    with open(all_path, 'w', encoding='utf-8') as f:
        f.write(header_all)
        f.write("\n".join(all_extra) + "\n")
        f.write("\n".join(sorted(tagged_set)) + "\n")
    logger.info(f"💾 ALL.txt: {len(tagged_set)}")

    # ---- LTE / WIFI ----
    whitelist = load_whitelist()
    cidr_list = load_cidr_whitelist()

    lte_set = set()
    wifi_set = set()
    for line in tagged_set:
        if get_config_priority(line, whitelist, cidr_list) in (0, 1):
            lte_set.add(line)
        else:
            wifi_set.add(line)

    lte_list = sorted(lte_set, key=lambda x: get_config_priority(x, whitelist, cidr_list))
    wifi_list = sorted(wifi_set)

    protocol_counts_lte = count_protocols(lte_set)
    protocol_counts_wifi = count_protocols(wifi_set)

    lte_extra = generate_extra_lines(len(lte_list), protocol_counts_lte, update_time, "LTE")
    lte_path = os.path.join(CONFIG_DIR, "LTE.txt")
    with open(lte_path, 'w', encoding='utf-8') as f:
        f.write(header_lte)
        f.write("\n".join(lte_extra) + "\n")
        f.write("\n".join(lte_list) + "\n")
    logger.info(f"📱 LTE.txt: {len(lte_list)}")

    wifi_extra = generate_extra_lines(len(wifi_list), protocol_counts_wifi, update_time, "WIFI")
    wifi_path = os.path.join(CONFIG_DIR, "WIFI.txt")
    with open(wifi_path, 'w', encoding='utf-8') as f:
        f.write(header_wifi)
        f.write("\n".join(wifi_extra) + "\n")
        f.write("\n".join(wifi_list) + "\n")
    logger.info(f"📶 WIFI.txt: {len(wifi_list)}")

    # ---- ESPD ----
    espd_path = None
    if espd_configs:
        espd_extra = generate_espd_lines(len(espd_configs), protocol_counts_espd, update_time)
        espd_path = os.path.join(CONFIG_DIR, "LinObhodESPD.txt")
        with open(espd_path, 'w', encoding='utf-8') as f:
            f.write(header_espd)
            f.write("\n".join(espd_extra) + "\n")
            f.write("\n".join(sorted(espd_configs)) + "\n")
        logger.info(f"🏫 LinObhodESPD.txt: {len(espd_configs)} (SNI: max.ru, api-maps.yandex.ru)")
    else:
        logger.info("⚠️ Нет конфигов для LinObhodESPD.txt")

    # ---- BASE64 ----
    def save_b64(original_path, suffix):
        b64_path = original_path.replace('.txt', f'.{suffix}.txt')
        with open(original_path, 'rb') as f:
            data = f.read()
        b64_data = base64.b64encode(data).decode('ascii')
        with open(b64_path, 'w', encoding='ascii') as f:
            f.write(b64_data)
        logger.info(f"🔐 {os.path.basename(b64_path)}: base64 закодирован (длина {len(b64_data)})")

    save_b64(all_path, '64')
    save_b64(lte_path, '64')
    save_b64(wifi_path, '64')

    if espd_configs and espd_path and os.path.exists(espd_path):
        espd_b64_path = os.path.join(CONFIG_DIR, "LinObhodESPD.64.txt")
        with open(espd_path, 'rb') as f:
            data = f.read()
        b64_data = base64.b64encode(data).decode('ascii')
        with open(espd_b64_path, 'w', encoding='ascii') as f:
            f.write(b64_data)
        logger.info(f"🔐 LinObhodESPD.64.txt: base64 закодирован (длина {len(b64_data)})")

    # ---- README ----
    update_readme(
        total=len(tagged_set),
        lte=len(lte_list),
        wifi=len(wifi_list),
        espd=len(espd_configs),
        protocols_all=protocol_counts_all,
        protocols_lte=protocol_counts_lte,
        protocols_wifi=protocol_counts_wifi,
        protocols_espd=protocol_counts_espd,
    )
    logger.info("✅ Готово.")


# === ЗАПУСК ===
async def main_async():
    start_time = time.time()
    print("=" * 60)
    print("🚀 LinSpisokObhod v3.10 (VMess-фикс, IPinfo, URL-encoded комментарии)")
    print("=" * 60)

    sources = load_sources_from_file("source.txt")
    if not sources:
        logger.error("❌ Нет источников для загрузки. Проверьте source.txt")
        return

    print(f"📋 Источников загружено из source.txt: {len(sources)}")
    print(f"📁 Результаты в папке: {CONFIG_DIR}")
    print(f"🌍 Геолокация: ВКЛЮЧЕНА (IPinfo, токенов: {len(IPINFO_TOKENS)})")
    print("=" * 60)

    contents = await fetch_all_sources(sources)
    configs_map = await collect_configs_async(contents)
    save_configs(configs_map)

    elapsed = time.time() - start_time
    print("\n" + "=" * 60)
    print("📊 ИТОГИ СБОРА:")
    print("=" * 60)
    print(f"📈 Всего уникальных: {len(configs_map)}")
    print(f"⏱️ Время: {elapsed:.2f} секунд")
    print("=" * 60)


def main():
    asyncio.run(main_async())


if __name__ == "__main__":
    # Быстрый self-test VMess (если задан TEST_VMESS=1)
    if os.environ.get("TEST_VMESS") == "1":
        _sample = {
            "v": "2", "ps": "test", "add": "1.2.3.4", "port": "443",
            "id": "uuid", "aid": "0", "scy": "auto",
            "net": "ws", "type": "none", "host": "example.com",
            "path": "/ws", "tls": "tls", "sni": "example.com",
        }
        _raw = "vmess://" + base64.b64encode(json.dumps(_sample).encode()).decode()
        _raw_nopad = _raw.rstrip('=') + "#Some%20name"
        for _cfg in (_raw, _raw_nopad):
            _d = decode_vmess_config(_cfg)
            assert _d and _d["add"] == "1.2.3.4", f"decode failed: {_cfg}"
            assert extract_host_from_config(_cfg) == "1.2.3.4"
            assert extract_sni_domain(_cfg) == "example.com"
            assert get_endpoint(_cfg) == ("1.2.3.4", 443)
            assert _vmess_transport(_d) == "WebSocket"
        print("✅ VMess self-test OK")
        raise SystemExit(0)

    try:
        main()
    except KeyboardInterrupt:
        logger.info("⏹️ Прерывание")
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
        raise
