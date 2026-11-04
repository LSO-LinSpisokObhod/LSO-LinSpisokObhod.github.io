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
from urllib.parse import parse_qs, quote, unquote
from typing import Dict, Set, Optional, List, Tuple

try:
    import yaml as _pyyaml
except ImportError:
    _pyyaml = None

# ========== НАСТРОЙКИ ==========
GEOIP_PARALLEL = 10
GEOIP_DELAY = 0.1
REQUEST_TIMEOUT = int(os.environ.get("REQUEST_TIMEOUT", "15"))

_env_tokens = [t.strip() for t in os.environ.get("IPINFO_TOKEN", "").split(",") if t.strip()]
IPINFO_TOKENS = _env_tokens or ["a94d8c011ca891"]
if not IPINFO_TOKENS:
    raise ValueError("No IPINFO_TOKEN provided.")

GEOIP_CACHE = {}
GEOIP_SEMAPHORE = asyncio.Semaphore(GEOIP_PARALLEL)
TOKEN_INDEX = 0
TOKEN_LOCK = asyncio.Lock()

CONFIG_DIR = "sub"
LISTS_DIR = "lists"
WHITELIST_FILE = os.path.join(LISTS_DIR, "whitelist.txt")
CIDR_WHITELIST_FILE = os.path.join(LISTS_DIR, "cidrwhitelist.txt")
GLOBAL_TAG = "[#LSO - #LinSpisokObhod]"

PROTOCOL_PATTERNS = {
    'vless':     re.compile(r'vless://[A-Za-z0-9+/=@:;,\?&%#\.\-_~!$*()]+', re.IGNORECASE),
    'vmess':     re.compile(r'vmess://[A-Za-z0-9+/=_-]+(?:#[^\s"\'`<>,;]+)?', re.IGNORECASE),
    'trojan':    re.compile(r'trojan://[A-Za-z0-9+/=@:;,\?&%#\.\-_~!$*()]+', re.IGNORECASE),
    'hysteria2': re.compile(r'(?:hysteria2|hy2)://[A-Za-z0-9+/=@:;,\?&%#\.\-_~!$*()]+', re.IGNORECASE),
}

PROTOCOL_PREFIXES = {
    'vless':     ('vless',),
    'vmess':     ('vmess',),
    'trojan':    ('trojan',),
    'hysteria2': ('hysteria2', 'hy2'),
}


def detect_protocol(config: str) -> Optional[str]:
    for proto, prefixes in PROTOCOL_PREFIXES.items():
        for prefix in prefixes:
            if config.startswith(prefix + "://"):
                return proto
    return None


def strip_protocol(config: str) -> str:
    for proto, prefixes in PROTOCOL_PREFIXES.items():
        for prefix in prefixes:
            if config.startswith(prefix + "://"):
                return config[len(prefix) + 3:]
    return config


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# === ЗАГРУЗКА ИСТОЧНИКОВ ===
def load_sources_from_file(path: str = "source.txt") -> List[str]:
    sources = []
    if not os.path.exists(path):
        logger.error(f"❌ Файл {path} не найден!")
        return sources
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                sources.append(line)
    return sources


# === TCP-ПРОВЕРКА ===
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


# === BASE64 ===
def decode_base64_if_needed(content: str) -> str:
    content = content.strip()
    if len(content) < 20:
        return content

    # Уже содержит протокол — декодировать нечего
    if '://' in content:
        return content

    # URL-encoded base64 (например, '%3D' в конце)
    if '%' in content:
        try:
            content = unquote(content)
        except Exception:
            pass

    def _try_decode(s: str) -> Optional[str]:
        s = re.sub(r'\s+', '', s)
        if not s:
            return None
        # base64url → base64
        s = s.replace('-', '+').replace('_', '/')
        s = re.sub(r'[^A-Za-z0-9+/=]', '', s)
        if not s:
            return None
        # Восстанавливаем padding (unpadded base64 — самый частый случай)
        s += '=' * ((-len(s)) % 4)
        try:
            decoded = base64.b64decode(s, validate=False)
            return decoded.decode('utf-8', errors='ignore')
        except Exception:
            return None

    decoded_str = _try_decode(content)
    if decoded_str is None:
        return content

    if '://' in decoded_str:
        return decoded_str

    # Бывает double-encoded: base64 от base64
    if len(decoded_str) >= 20:
        nested = _try_decode(decoded_str)
        if nested is not None and '://' in nested:
            return nested

    if decoded_str.isprintable() and len(decoded_str) > 50:
        return decoded_str

    return content


# === ЗАГРУЗКА ===
async def fetch_url_content(session: aiohttp.ClientSession, url: str,
                             attempt: int = 0, retries: int = 1) -> Optional[str]:
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        async with session.get(url, timeout=REQUEST_TIMEOUT, headers=headers) as response:
            if response.status == 200:
                content = await response.text()
                content = decode_base64_if_needed(content)
                logger.info(f"📦 {url} -> длина {len(content)}, начало: {content[:200]}")
                return content
            logger.warning(f"⚠️ HTTP {response.status}: {url}")
            return None
    except asyncio.TimeoutError:
        logger.warning(f"⏱ Таймаут {REQUEST_TIMEOUT}s: {url}")
    except aiohttp.ClientConnectorError as e:
        logger.warning(f"🔌 DNS/connect: {url} — {e}")
    except aiohttp.ClientResponseError as e:
        logger.warning(f"🌐 HTTP {e.status}: {url}")
    except aiohttp.ClientPayloadError as e:
        logger.warning(f"📦 Payload: {url} — {e!r}")
    except aiohttp.ClientError as e:
        logger.warning(f"🌐 {type(e).__name__}: {url} — {e!r}")
    except Exception as e:
        logger.warning(f"❌ {type(e).__name__}: {url} — {e!r}")

    if attempt < retries:
        await asyncio.sleep(2 ** attempt)
        return await fetch_url_content(session, url, attempt + 1, retries)
    return None


async def fetch_all_sources(sources: List[str]):
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_url_content(session, url) for url in sources]
        results = await asyncio.gather(*tasks)
    return dict(zip(sources, results))


# === ПАРСИНГ ===
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


# === VMESS ===
def _vmess_b64_normalize(s: str) -> str:
    s = s.strip()
    if '%' in s:
        try:
            s = unquote(s)
        except Exception:
            pass
    s = s.replace('-', '+').replace('_', '/')
    s = re.sub(r'[^A-Za-z0-9+/=]', '', s)
    pad = (-len(s)) % 4
    if pad:
        s += '=' * pad
    return s


def decode_vmess_config(config: str) -> Optional[Dict]:
    if not config.startswith('vmess://'):
        return None
    payload = config[8:]
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
    add = data.get('add')
    if not isinstance(add, str) or not add.strip():
        return None
    return data


def _vmess_host(data: Dict) -> Optional[str]:
    host = data.get('add')
    if not isinstance(host, str):
        return None
    host = host.strip().strip('[]')
    return host or None


def _vmess_port(data: Dict, default: int = 443) -> int:
    raw = data.get('port')
    try:
        port = int(raw)
        if 1 <= port <= 65535:
            return port
    except (TypeError, ValueError):
        pass
    return default


def _vmess_sni(data: Dict) -> Optional[str]:
    for key in ('sni', 'host'):
        v = data.get(key)
        if isinstance(v, str) and v.strip():
            return v.strip()
    return None


def _vmess_transport(data: Dict) -> str:
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
    if protocol == 'vmess':
        data = decode_vmess_config(config)
        return _vmess_host(data) if data else None
    body = strip_protocol(config)
    if '@' not in body:
        return None
    host_part = body.split('@', 1)[1]
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
        # 'peer' — стандартный ключ SNI в hysteria2
        for key in ('sni', 'host', 'peer'):
            if key in params and params[key]:
                return params[key][0]
    return None


def get_endpoint(cfg: str) -> Optional[Tuple[str, int]]:
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


# === ФИЛЬТР: fp=chrome → firefox ===
def _url_fp(config: str) -> Optional[str]:
    body = strip_protocol(config)
    if '?' not in body:
        return None
    query = body.split('?', 1)[1].split('#', 1)[0]
    if not query:
        return None
    params = parse_qs(query)
    fp = params.get('fp', [''])[0] or ''
    return fp.strip().lower() or None


def _vmess_fp(config: str) -> Optional[str]:
    data = decode_vmess_config(config)
    if not data:
        return None
    fp = data.get('fp')
    if not isinstance(fp, str):
        return None
    return fp.strip().lower() or None


def is_fp_chrome(config: str) -> bool:
    protocol = detect_protocol(config)
    if not protocol:
        return False
    if protocol == 'vmess':
        return _vmess_fp(config) == 'chrome'
    return _url_fp(config) == 'chrome'


# === ЗАМЕНА fp=chrome → fp=firefox ===
def replace_fp_chrome(config: str) -> str:
    """Заменяет fp=chrome на fp=firefox. Возвращает исходный конфиг, если fp=chrome нет."""
    protocol = detect_protocol(config)
    if not protocol:
        return config
    if protocol == 'vmess':
        return _vmess_replace_fp_chrome(config)
    return _url_replace_fp_chrome(config)


def _url_replace_fp_chrome(config: str) -> str:
    # Отделяем фрагмент (комментарий)
    if '#' in config:
        base, frag = config.split('#', 1)
        fragment = '#' + frag
    else:
        base = config
        fragment = ''

    if '?' not in base:
        return config

    body_main, query = base.split('?', 1)
    if not query:
        return config

    parts = query.split('&')
    changed = False
    for i, part in enumerate(parts):
        if '=' in part:
            k, _, v = part.partition('=')
            if k == 'fp' and unquote(v).strip().lower() == 'chrome':
                parts[i] = k + '=firefox'
                changed = True

    if not changed:
        return config

    return body_main + '?' + '&'.join(parts) + fragment


def _vmess_replace_fp_chrome(config: str) -> str:
    data = decode_vmess_config(config)
    if not data:
        return config

    fp = data.get('fp')
    if not isinstance(fp, str) or fp.strip().lower() != 'chrome':
        return config

    data['fp'] = 'firefox'

    fragment = ''
    if '#' in config:
        _, fragment = config.rsplit('#', 1)

    try:
        payload = base64.b64encode(
            json.dumps(data, ensure_ascii=False).encode('utf-8')
        ).decode('ascii')
    except Exception:
        return config

    result = 'vmess://' + payload
    if fragment:
        result += '#' + fragment
    return result


# === ДЕДУБЛИКАЦИЯ ===
_VMESS_IDENTITY_KEYS = (
    'add', 'port', 'id', 'aid', 'scy',
    'net', 'type', 'host', 'path',
    'tls', 'sni', 'alpn', 'fp',
)
_URL_IGNORED_PARAMS = {'remarks', 'name', 'remark', 'label', 'ps'}


def _vmess_canonical_key(data: Dict) -> str:
    parts = []
    for k in _VMESS_IDENTITY_KEYS:
        v = data.get(k, '')
        if v is None:
            v = ''
        if k in ('port', 'aid'):
            # Нормализуем к int — иначе "443" != 443, дубликаты не склеиваются
            try:
                v = int(v)
            except (TypeError, ValueError):
                v = 0
        elif isinstance(v, (dict, list)):
            v = json.dumps(v, sort_keys=True, ensure_ascii=False)
        else:
            v = str(v).strip()
        if k == 'add':
            v = str(v).lower().strip('[]')
        parts.append(f"{k}={v}")
    return 'vmess://' + '|'.join(parts)


def _url_config_canonical_key(config: str, protocol: str) -> str:
    body = strip_protocol(config)
    if '?' in body:
        body_main, query = body.split('?', 1)
    else:
        body_main, query = body, ''

    user = ''
    host = ''
    port = ''
    if '@' in body_main:
        user, hostport = body_main.split('@', 1)
    else:
        hostport = body_main

    if hostport.startswith('['):
        end = hostport.find(']')
        host = hostport[1:end].lower()
        rest = hostport[end + 1:]
        if rest.startswith(':'):
            port = rest[1:]
    elif ':' in hostport:
        host, port = hostport.rsplit(':', 1)
        host = host.lower()
    else:
        host = hostport.lower()

    params = {}
    if query:
        for pair in query.split('&'):
            if not pair:
                continue
            k, _, v = pair.partition('=')
            k = k.strip()
            if not k or k.lower() in _URL_IGNORED_PARAMS:
                continue
            params[k] = v
    sorted_params = '&'.join(f"{k}={params[k]}" for k in sorted(params))

    proto_key = 'hysteria2' if protocol == 'hysteria2' else protocol
    return f"{proto_key}://{user}@{host}:{port}?{sorted_params}"


def get_config_key(config: str) -> str:
    config = config.strip()
    if '#' in config:
        config = config.split('#', 1)[0].strip()
    protocol = detect_protocol(config)
    if not protocol:
        return config.lower()
    if protocol == 'vmess':
        data = decode_vmess_config(config)
        if data:
            return _vmess_canonical_key(data)
        return config.lower()
    return _url_config_canonical_key(config, protocol)


def deduplicate_configs(configs: List[str]) -> List[str]:
    seen_keys: Dict[str, str] = {}
    unique_configs: List[str] = []
    duplicates_count = 0
    for cfg in configs:
        key = get_config_key(cfg)
        if key not in seen_keys:
            seen_keys[key] = cfg
            unique_configs.append(cfg)
        else:
            duplicates_count += 1
            logger.debug(f"🔁 dup: {cfg[:80]}…")
    if duplicates_count > 0:
        logger.info(f"🔁 Удалено дубликатов: {duplicates_count} (осталось {len(unique_configs)})")
    return unique_configs


# === ГЕОЛОКАЦИЯ ===
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
    logger.info(f"🌍 Определяю страны для {total} уникальных IP через IPinfo")
    processed = 0
    async with aiohttp.ClientSession() as session:
        tasks = [resolve_country(ip, session) for ip in unique_ips]
        for future in asyncio.as_completed(tasks):
            await future
            processed += 1
            if processed % 100 == 0 or processed == total:
                logger.info(f"   Прогресс геолокации: {processed}/{total} IP")
            await asyncio.sleep(GEOIP_DELAY)
    logger.info("✅ Геолокация завершена")
    return GEOIP_CACHE.copy()


# === ПЕРЕИМЕНОВАНИЕ ===
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
            f.write("#   .yandex        — любой домен с лейблом 'yandex'\n")
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
                if domain.endswith(a):
                    return True
            else:
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


# === YAML (Clash Meta) ===
def _url_params(config: str) -> Dict[str, str]:
    body = strip_protocol(config)
    if '?' not in body:
        return {}
    query = body.split('?', 1)[1].split('#', 1)[0]
    out = {}
    for pair in query.split('&'):
        if not pair:
            continue
        k, _, v = pair.partition('=')
        out[k] = unquote(v)
    return out


def _decode_comment(config: str) -> str:
    if '#' not in config:
        return ''
    return unquote(config.rsplit('#', 1)[1])


def _user_from_url(config: str) -> str:
    body = strip_protocol(config)
    m = re.match(r'([^@]+)@', body)
    return m.group(1) if m else ''


def _port_from_url(config: str, default: int = 443) -> int:
    body = strip_protocol(config)
    m = re.search(r'@[^:]+:(\d+)', body)
    return int(m.group(1)) if m else default


def _vless_to_clash(config: str) -> Optional[Dict]:
    host = extract_host_from_config(config)
    if not host:
        return None
    params = _url_params(config)
    proxy = {
        'name': _decode_comment(config) or f'VLESS-{host}',
        'type': 'vless',
        'server': host,
        'port': _port_from_url(config),
        'uuid': _user_from_url(config),
        'udp': True,
    }
    sec = (params.get('security') or '').lower()
    if sec in ('tls', 'reality'):
        proxy['tls'] = True
    if sec == 'reality':
        ro = {}
        if 'pbk' in params:
            ro['public-key'] = params['pbk']
        if 'sid' in params:
            ro['short-id'] = params['sid']
        if ro:
            proxy['reality-opts'] = ro
    if 'sni' in params:
        proxy['servername'] = params['sni']
    if 'fp' in params:
        proxy['client-fingerprint'] = params['fp']
    if 'flow' in params:
        proxy['flow'] = params['flow']
    net = (params.get('type') or 'tcp').lower()
    if net == 'ws':
        proxy['network'] = 'ws'
        wo = {'path': params.get('path', '/')}
        if 'host' in params:
            wo['headers'] = {'Host': params['host']}
        proxy['ws-opts'] = wo
    elif net == 'grpc':
        proxy['network'] = 'grpc'
        proxy['grpc-opts'] = {'grpc-service-name': params.get('serviceName', '')}
    elif net not in ('tcp', ''):
        proxy['network'] = net
    return proxy


def _vmess_to_clash(config: str) -> Optional[Dict]:
    data = decode_vmess_config(config)
    if not data:
        return None
    try:
        port = int(data.get('port', 443))
    except (ValueError, TypeError):
        port = 443
    try:
        aid = int(data.get('aid', 0))
    except (ValueError, TypeError):
        aid = 0
    name = _decode_comment(config) or data.get('ps') or f"VMess-{data.get('add', '?')}"
    proxy = {
        'name': name,
        'type': 'vmess',
        'server': data.get('add', ''),
        'port': port,
        'uuid': data.get('id', ''),
        'alterId': aid,
        'cipher': data.get('scy') or 'auto',
        'udp': True,
    }
    if data.get('tls') == 'tls':
        proxy['tls'] = True
    if data.get('sni'):
        proxy['servername'] = data['sni']
    elif data.get('host'):
        proxy['servername'] = data['host']
    net = (data.get('net') or 'tcp').lower()
    if net == 'ws':
        proxy['network'] = 'ws'
        wo = {'path': data.get('path', '/')}
        if data.get('host'):
            wo['headers'] = {'Host': data['host']}
        proxy['ws-opts'] = wo
    elif net == 'grpc':
        proxy['network'] = 'grpc'
        proxy['grpc-opts'] = {'grpc-service-name': data.get('path', '')}
    elif net not in ('tcp', ''):
        proxy['network'] = net
    return proxy


def _trojan_to_clash(config: str) -> Optional[Dict]:
    host = extract_host_from_config(config)
    if not host:
        return None
    params = _url_params(config)
    proxy = {
        'name': _decode_comment(config) or f'Trojan-{host}',
        'type': 'trojan',
        'server': host,
        'port': _port_from_url(config),
        'password': _user_from_url(config),
        'udp': True,
        'skip-cert-verify': params.get('allowInsecure', '0') == '1',
    }
    if 'sni' in params:
        proxy['sni'] = params['sni']
    if 'fp' in params:
        proxy['client-fingerprint'] = params['fp']
    net = (params.get('type') or 'tcp').lower()
    if net == 'ws':
        proxy['network'] = 'ws'
        wo = {'path': params.get('path', '/')}
        if 'host' in params:
            wo['headers'] = {'Host': params['host']}
        proxy['ws-opts'] = wo
    elif net == 'grpc':
        proxy['network'] = 'grpc'
        proxy['grpc-opts'] = {'grpc-service-name': params.get('serviceName', '')}
    return proxy


def _hysteria2_to_clash(config: str) -> Optional[Dict]:
    host = extract_host_from_config(config)
    if not host:
        return None
    params = _url_params(config)
    proxy = {
        'name': _decode_comment(config) or f'HY2-{host}',
        'type': 'hysteria2',
        'server': host,
        'port': _port_from_url(config),
        'password': _user_from_url(config),
        'udp': True,
        'skip-cert-verify': params.get('insecure', '0') == '1',
    }
    if 'sni' in params:
        proxy['sni'] = params['sni']
    if 'obfs' in params:
        proxy['obfs'] = params['obfs']
        if 'obfs-password' in params:
            proxy['obfs-password'] = params['obfs-password']
    return proxy


def parse_uri_to_clash(config: str) -> Optional[Dict]:
    protocol = detect_protocol(config)
    if not protocol:
        return None
    try:
        if protocol == 'vless':     return _vless_to_clash(config)
        if protocol == 'vmess':     return _vmess_to_clash(config)
        if protocol == 'trojan':    return _trojan_to_clash(config)
        if protocol == 'hysteria2': return _hysteria2_to_clash(config)
    except Exception as e:
        logger.debug(f'YAML parse fail {config[:60]}: {e}')
    return None


def build_clash_yaml(configs: Set[str], extra_lines: List[str] = None) -> str:
    proxies = []
    if extra_lines:
        for cfg in extra_lines:
            p = parse_uri_to_clash(cfg)
            if p:
                proxies.append(p)
                
    for cfg in sorted(configs):
        p = parse_uri_to_clash(cfg)
        if p:
            proxies.append(p)
            
    doc = {'proxies': proxies}
    if _pyyaml is None:
        return json.dumps(doc, ensure_ascii=False, indent=2)
    return _pyyaml.safe_dump(
        doc,
        allow_unicode=True,
        sort_keys=False,
        default_flow_style=False,
        width=10000,
    )


# === sing-box (JSON) ===
def _vless_to_singbox(config: str) -> Optional[Dict]:
    host = extract_host_from_config(config)
    if not host:
        return None
    params = _url_params(config)
    ob = {
        'type': 'vless',
        'tag': _decode_comment(config) or f'vless-{host}',
        'server': host,
        'server_port': _port_from_url(config),
        'uuid': _user_from_url(config),
    }
    if 'flow' in params:
        ob['flow'] = params['flow']
    sec = (params.get('security') or '').lower()
    if sec in ('tls', 'reality'):
        tls = {'enabled': True}
        if 'sni' in params:
            tls['server_name'] = params['sni']
        if 'alpn' in params:
            tls['alpn'] = params['alpn'].split(',')
        if params.get('allowInsecure', '0') == '1' or params.get('insecure', '0') == '1':
            tls['insecure'] = True
        if sec == 'reality':
            reality = {'enabled': True}
            if 'pbk' in params:
                reality['public_key'] = params['pbk']
            if 'sid' in params:
                reality['short_id'] = params['sid']
            tls['reality'] = reality
        if 'fp' in params:
            tls['utls'] = {'enabled': True, 'fingerprint': params['fp'].lower()}
        ob['tls'] = tls
    net = (params.get('type') or 'tcp').lower()
    if net == 'ws':
        tr = {'type': 'ws', 'path': params.get('path', '/')}
        if 'host' in params:
            tr['headers'] = {'Host': params['host']}
        ob['transport'] = tr
    elif net == 'grpc':
        ob['transport'] = {'type': 'grpc', 'service_name': params.get('serviceName', '')}
    return ob


def _vmess_to_singbox(config: str) -> Optional[Dict]:
    data = decode_vmess_config(config)
    if not data:
        return None
    try:
        port = int(data.get('port', 443))
    except (ValueError, TypeError):
        port = 443
    try:
        aid = int(data.get('aid', 0))
    except (ValueError, TypeError):
        aid = 0
    ob = {
        'type': 'vmess',
        'tag': _decode_comment(config) or data.get('ps') or f"vmess-{data.get('add', '?')}",
        'server': data.get('add', ''),
        'server_port': port,
        'uuid': data.get('id', ''),
        'security': data.get('scy') or 'auto',
        'alter_id': aid,
    }
    if data.get('tls') == 'tls':
        tls = {'enabled': True}
        if data.get('sni'):
            tls['server_name'] = data['sni']
        elif data.get('host'):
            tls['server_name'] = data['host']
        ob['tls'] = tls
    net = (data.get('net') or 'tcp').lower()
    if net == 'ws':
        tr = {'type': 'ws', 'path': data.get('path', '/')}
        if data.get('host'):
            tr['headers'] = {'Host': data['host']}
        ob['transport'] = tr
    elif net == 'grpc':
        ob['transport'] = {'type': 'grpc', 'service_name': data.get('path', '')}
    return ob


def _trojan_to_singbox(config: str) -> Optional[Dict]:
    host = extract_host_from_config(config)
    if not host:
        return None
    params = _url_params(config)
    ob = {
        'type': 'trojan',
        'tag': _decode_comment(config) or f'trojan-{host}',
        'server': host,
        'server_port': _port_from_url(config),
        'password': _user_from_url(config),
    }
    tls = {'enabled': True}
    if 'sni' in params:
        tls['server_name'] = params['sni']
    if params.get('allowInsecure', '0') == '1' or params.get('insecure', '0') == '1':
        tls['insecure'] = True
    if 'fp' in params:
        tls['utls'] = {'enabled': True, 'fingerprint': params['fp'].lower()}
    ob['tls'] = tls
    net = (params.get('type') or 'tcp').lower()
    if net == 'ws':
        tr = {'type': 'ws', 'path': params.get('path', '/')}
        if 'host' in params:
            tr['headers'] = {'Host': params['host']}
        ob['transport'] = tr
    return ob


def _hysteria2_to_singbox(config: str) -> Optional[Dict]:
    host = extract_host_from_config(config)
    if not host:
        return None
    params = _url_params(config)
    ob = {
        'type': 'hysteria2',
        'tag': _decode_comment(config) or f'hy2-{host}',
        'server': host,
        'server_port': _port_from_url(config),
        'password': _user_from_url(config),
    }
    tls = {'enabled': True}
    if 'sni' in params:
        tls['server_name'] = params['sni']
    if 'alpn' in params:
        tls['alpn'] = params['alpn'].split(',')
    if params.get('insecure', '0') == '1':
        tls['insecure'] = True
    ob['tls'] = tls
    if 'obfs' in params:
        ob['obfs'] = {'type': params['obfs'], 'password': params.get('obfs-password', '')}
    return ob


def parse_uri_to_singbox(config: str) -> Optional[Dict]:
    protocol = detect_protocol(config)
    if not protocol:
        return None
    try:
        if protocol == 'vless':     return _vless_to_singbox(config)
        if protocol == 'vmess':     return _vmess_to_singbox(config)
        if protocol == 'trojan':    return _trojan_to_singbox(config)
        if protocol == 'hysteria2': return _hysteria2_to_singbox(config)
    except Exception as e:
        logger.debug(f'sing-box parse fail {config[:60]}: {e}')
    return None


def build_singbox_json(configs: Set[str], extra_lines: List[str] = None) -> str:
    outbounds = []
    
    if extra_lines:
        for cfg in extra_lines:
            ob = parse_uri_to_singbox(cfg)
            if ob:
                outbounds.append(ob)
                
    for cfg in sorted(configs):
        ob = parse_uri_to_singbox(cfg)
        if ob:
            outbounds.append(ob)
            
    outbounds.append({'type': 'direct', 'tag': 'direct'})
    outbounds.append({'type': 'block', 'tag': 'block'})

    doc = {
        'log': {'level': 'info', 'timestamp': True},
        'dns': {
            'servers': [
                {'tag': 'cloudflare', 'address': 'https://1.1.1.1/dns-query'},
                {'tag': 'google', 'address': 'https://8.8.8.8/dns-query'},
                {'tag': 'local', 'address': 'local', 'detour': 'direct'},
            ],
            'final': 'cloudflare',
            'strategy': 'prefer_ipv4',
        },
        'inbounds': [
            {'type': 'mixed', 'tag': 'mixed-in', 'listen': '127.0.0.1', 'listen_port': 2080},
        ],
        'outbounds': outbounds,
        'route': {
            'rules': [],
            'final': 'direct',
            'auto_detect_interface': True,
        },
    }
    return json.dumps(doc, ensure_ascii=False, indent=2)


# === ОСНОВНОЙ СБОР ===
async def collect_configs_async(contents: Dict[str, Optional[str]]) -> Dict[str, Tuple[str, str]]:
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

    # Замена fp=chrome → fp=firefox (до дедубликации)
    _fp_replaced = 0
    _new_configs = []
    for c in raw_configs:
        r = replace_fp_chrome(c)
        if r != c:
            _fp_replaced += 1
        _new_configs.append(r)
    raw_configs = _new_configs
    if _fp_replaced:
        logger.info(f"🔧 Заменено fp=chrome → fp=firefox: {_fp_replaced} конфигов")

    raw_configs = deduplicate_configs(raw_configs)
    logger.info(f"🔄 После дедубликации: {len(raw_configs)}")

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
                        logger.info(f"⏳ Прогресс TCP-тестирования: {checked_count}/{total_endpoints}")
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

    if all_ips:
        await resolve_countries_parallel(list(all_ips))
    else:
        logger.info("🌍 Геолокация: IP для определения не найдены")

    configs_map: Dict[str, Tuple[str, str]] = {}
    for i, cfg in enumerate(raw_configs, 1):
        ip = extract_ip_from_config(cfg)
        country = GEOIP_CACHE.get(ip, '') if ip else ''
        renamed_cfg = rename_config(cfg, country, tag=GLOBAL_TAG)
        if renamed_cfg not in configs_map:
            configs_map[renamed_cfg] = (cfg, country)
        if i % 500 == 0 or i == len(raw_configs):
            logger.info(f"⏳ Прогресс переименования: {i}/{len(raw_configs)}")

    logger.info(f"📊 Собрано уникальных конфигов: {len(configs_map)}")
    return configs_map


# === README ===
def update_readme(total: int, lte: int, wifi: int,
                 protocols_all: Dict[str, int],
                 protocols_lte: Dict[str, int],
                 protocols_wifi: Dict[str, int]):
    moscow_time = get_moscow_time()

    readme_content = f"""# 🚀 LinSpisokObhod

## 📅 Время последнего сбора

`{moscow_time} (UTC+3)`

---

## 📊 Статистика по файлам

| Файл | Всего конфигов |
|------|----------------|
| 📁 ALL.txt / ALL.yml / ALL.json | `{total}` |
| 📱 LTE.txt / LTE.yml / LTE.json | `{lte}` |
| 📶 WIFI.txt / WIFI.yml / WIFI.json | `{wifi}` |

---

## 📡 Статистика по протоколам

### 🌐 ALL

| Протокол | Количество |
|----------|------------|
| 🔗 VLESS | `{protocols_all.get('vless', 0)}` |
| 📦 VMess | `{protocols_all.get('vmess', 0)}` |
| 🛡️ Trojan | `{protocols_all.get('trojan', 0)}` |
| ⚡ Hysteria2 | `{protocols_all.get('hysteria2', 0)}` |
| **ИТОГО** | **`{total}`** |

### 📱 LTE

| Протокол | Количество |
|----------|------------|
| 🔗 VLESS | `{protocols_lte.get('vless', 0)}` |
| 📦 VMess | `{protocols_lte.get('vmess', 0)}` |
| 🛡️ Trojan | `{protocols_lte.get('trojan', 0)}` |
| ⚡ Hysteria2 | `{protocols_lte.get('hysteria2', 0)}` |
| **ИТОГО** | **`{lte}`** |

### 📶 WIFI

| Протокол | Количество |
|----------|------------|
| 🔗 VLESS | `{protocols_wifi.get('vless', 0)}` |
| 📦 VMess | `{protocols_wifi.get('vmess', 0)}` |
| 🛡️ Trojan | `{protocols_wifi.get('trojan', 0)}` |
| ⚡ Hysteria2 | `{protocols_wifi.get('hysteria2', 0)}` |
| **ИТОГО** | **`{wifi}`** |

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
"""
    with open("README.md", 'w', encoding='utf-8') as f:
        f.write(readme_content)
    logger.info("📄 README.md обновлён")


def get_moscow_time() -> str:
    moscow_tz = timezone(timedelta(hours=3))
    now_msk = datetime.now(moscow_tz)
    return now_msk.strftime("%Y-%m-%d %H:%M:%S")


# === ЗАГЛУШКИ (INFO-НОДЫ) ===
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


# === СОХРАНЕНИЕ ===
def save_configs(configs_map: Dict[str, Tuple[str, str]]):
    if os.path.exists(CONFIG_DIR):
        shutil.rmtree(CONFIG_DIR)
        logger.info(f"🗑️ Папка {CONFIG_DIR} удалена")
    os.makedirs(CONFIG_DIR, exist_ok=True)
    logger.info(f"📁 Папка {CONFIG_DIR} создана заново")

    update_time = get_moscow_time()
    tagged_set: Set[str] = set(configs_map.keys())

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

    # ---- BASE64 (только .txt) ----
    def save_b64(original_path, suffix):
        b64_path = original_path.replace('.txt', f'.{suffix}.txt')
        with open(original_path, 'rb') as f:
            data = f.read()
        b64_data = base64.b64encode(data).decode('ascii')
        with open(b64_path, 'w', encoding='ascii') as f:
            f.write(b64_data)
        logger.info(f"🔐 {os.path.basename(b64_path)}: base64 (длина {len(b64_data)})")

    save_b64(all_path, '64')
    save_b64(lte_path, '64')
    save_b64(wifi_path, '64')

    # ---- YAML (Clash Meta) - plain only ----
    def save_yaml(configs_set: Set[str], extra_lines: List[str], base_name: str) -> str:
        content = build_clash_yaml(configs_set, extra_lines)
        yml_path = os.path.join(CONFIG_DIR, f"{base_name}.yml")
        with open(yml_path, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.info(f"📦 {base_name}.yml: {len(configs_set)} прокси (plain)")
        return yml_path

    save_yaml(tagged_set, all_extra, "ALL")
    save_yaml(lte_set, lte_extra, "LTE")
    save_yaml(wifi_set, wifi_extra, "WIFI")

    # ---- sing-box JSON - plain only ----
    def save_singbox(configs_set: Set[str], extra_lines: List[str], base_name: str) -> str:
        content = build_singbox_json(configs_set, extra_lines)
        json_path = os.path.join(CONFIG_DIR, f"{base_name}.json")
        with open(json_path, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.info(f"⚙️ {base_name}.json: sing-box ({len(configs_set)} прокси, plain)")
        return json_path

    save_singbox(tagged_set, all_extra, "ALL")
    save_singbox(lte_set, lte_extra, "LTE")
    save_singbox(wifi_set, wifi_extra, "WIFI")

    # ---- README ----
    update_readme(
        total=len(tagged_set),
        lte=len(lte_list),
        wifi=len(wifi_list),
        protocols_all=protocol_counts_all,
        protocols_lte=protocol_counts_lte,
        protocols_wifi=protocol_counts_wifi,
    )
    logger.info("✅ Готово.")


# === ЗАПУСК ===
async def main_async():
    start_time = time.time()
    print("=" * 60)
    print("🚀 LinSpisokObhod v4.2 (Без ESPD)")
    print("=" * 60)

    sources = load_sources_from_file("source.txt")
    if not sources:
        logger.error("❌ Нет источников для загрузки. Проверьте source.txt")
        return

    print(f"📋 Источников загружено из source.txt: {len(sources)}")
    print(f"📁 Результаты в папке: {CONFIG_DIR}")
    print(f"🌍 Геолокация: ВКЛЮЧЕНА (IPinfo, токенов: {len(IPINFO_TOKENS)})")
    print(f"🔧 Трансформация: fp=chrome → fp=firefox")
    print(f"📦 Форматы: .txt (URI), .yml (Clash Meta), .json (sing-box)")
    print(f"🔐 Base64: только .64.txt (yml/json — plain)")
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
            assert _d and _d["add"] == "1.2.3.4"
            assert extract_host_from_config(_cfg) == "1.2.3.4"
            assert extract_sni_domain(_cfg) == "example.com"
            assert get_endpoint(_cfg) == ("1.2.3.4", 443)

        _samples = [
            "vless://uuid@host.com:443?type=tcp&sni=x.com",
            "vless://uuid@host.com:443?sni=x.com&type=tcp",
            "vless://uuid@host.com:443?type=tcp&remarks=best",
        ]
        assert len({get_config_key(s) for s in _samples}) == 1
        assert get_config_key("hy2://u@h:443?x=1") == get_config_key("hysteria2://u@h:443?x=1")

        assert is_fp_chrome("vless://u@h:443?security=reality&fp=chrome&sni=x.com")
        assert not is_fp_chrome("vless://u@h:443?security=reality&fp=firefox&sni=x.com")
        assert is_fp_chrome("trojan://u@h:443?fp=chrome&sni=x.com")
        assert is_fp_chrome("hy2://u@h:443?fp=chrome&sni=x.com")

        _vm_c = dict(_sample); _vm_c["fp"] = "chrome"
        _vm_f = dict(_sample); _vm_f["fp"] = "firefox"
        _cfg_c = "vmess://" + base64.b64encode(json.dumps(_vm_c).encode()).decode()
        _cfg_f = "vmess://" + base64.b64encode(json.dumps(_vm_f).encode()).decode()
        assert is_fp_chrome(_cfg_c)
        assert not is_fp_chrome(_cfg_f)

        # Замена fp=chrome → fp=firefox
        _r = replace_fp_chrome("vless://u@h:443?security=tls&fp=chrome&sni=x.com#Tag")
        assert 'fp=firefox' in _r and 'fp=chrome' not in _r and _r.endswith('#Tag')
        assert replace_fp_chrome("vless://u@h:443?fp=firefox") == "vless://u@h:443?fp=firefox"
        assert replace_fp_chrome("vless://u@h:443?sni=x.com") == "vless://u@h:443?sni=x.com"

        _vm_r = replace_fp_chrome(_cfg_c)
        _d_r = decode_vmess_config(_vm_r)
        assert _d_r and _d_r.get("fp") == "firefox"
        assert replace_fp_chrome(_cfg_f) == _cfg_f

        _clash = parse_uri_to_clash("vless://uuid@host.com:443?security=tls&sni=x.com&type=ws&path=%2Fws&host=x.com")
        assert _clash and _clash['type'] == 'vless'
        assert _clash['network'] == 'ws'

        _sb = parse_uri_to_singbox("vless://uuid@host.com:443?security=tls&sni=x.com&type=ws&path=%2Fws&host=x.com")
        assert _sb and _sb['type'] == 'vless'
        assert _sb['transport']['type'] == 'ws'

        _extra = ["vless://update@update.lso:443?security=tls&sni=update.lso#Hello"]
        _yml = build_clash_yaml({"vless://uuid@host.com:443?security=tls&sni=x.com"}, _extra)
        assert 'proxies:' in _yml and 'Hello' in _yml

        _json = build_singbox_json({"vless://uuid@host.com:443?security=tls&sni=x.com"}, _extra)
        _parsed = json.loads(_json)
        assert 'outbounds' in _parsed and 'Hello' in _parsed['outbounds'][0]['tag']

        print("✅ Все self-tests OK")
        raise SystemExit(0)

    try:
        main()
    except KeyboardInterrupt:
        logger.info("⏹️ Прерывание")
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
        raise