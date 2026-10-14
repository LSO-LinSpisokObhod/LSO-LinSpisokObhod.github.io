#!/usr/bin/env python3
"""
Асинхронный нагрузочный генератор с подсчётом пакетов в секунду.

По умолчанию бьёт по http://y992103m.beget.tech (свой проект LinMarket).
Управление:
  --url        URL (по умолчанию http://y992103m.beget.tech)
  --rps        целевое число запросов в секунду
  --duration   длительность в секундах (0 = бесконечно, до Ctrl+C)
  --method     HTTP-метод (GET/POST/...)
  --insecure   не проверять TLS-сертификат

Ctrl+C — остановка и итоговая статистика.
"""

import argparse
import asyncio
import ssl
import time
from collections import deque

import aiohttp


class Stats:
    def __init__(self, window_seconds: float = 1.0):
        self.total = 0
        self.ok = 0
        self.errors = 0
        self.status_codes = {}
        self.window_seconds = window_seconds
        self.window = deque()
        self.latencies = deque(maxlen=20000)
        self.bytes_sent = 0
        self.bytes_received = 0
        self.bw_window = deque()
        self.start_time = time.monotonic()

    def record_request_sent(self):
        now = time.monotonic()
        self.window.append(now)
        cutoff = now - self.window_seconds
        while self.window and self.window[0] < cutoff:
            self.window.popleft()

    def record_bytes(self, sent: int, received: int):
        now = time.monotonic()
        self.bytes_sent += sent
        self.bytes_received += received
        self.bw_window.append((now, sent, received))
        cutoff = now - self.window_seconds
        while self.bw_window and self.bw_window[0][0] < cutoff:
            self.bw_window.popleft()

    def record_result(self, status, latency: float):
        self.total += 1
        self.latencies.append(latency)
        if status is None:
            self.errors += 1
        else:
            self.status_codes[status] = self.status_codes.get(status, 0) + 1
            if 200 <= status < 400:
                self.ok += 1
            else:
                self.errors += 1

    @property
    def packets_per_second(self) -> float:
        return len(self.window) / self.window_seconds

    @property
    def bytes_per_second(self):
        sent = sum(s for _, s, _ in self.bw_window) / self.window_seconds
        recv = sum(r for _, _, r in self.bw_window) / self.window_seconds
        return sent, recv

    def avg_latency(self) -> float:
        return sum(self.latencies) / len(self.latencies) if self.latencies else 0.0

    def p95_latency(self) -> float:
        if not self.latencies:
            return 0.0
        data = sorted(self.latencies)
        return data[max(0, int(len(data) * 0.95) - 1)]

    def report(self) -> str:
        elapsed = time.monotonic() - self.start_time
        codes = ", ".join(f"{k}:{v}" for k, v in sorted(self.status_codes.items()))
        sent_bps, recv_bps = self.bytes_per_second
        return (
            f"[{elapsed:6.1f}s] "
            f"RPS(пакеты/с)={self.packets_per_second:9.1f} | "
            f"всего={self.total:9d} | "
            f"ok={self.ok:9d} | "
            f"ошибок={self.errors:6d} | "
            f"ср={self.avg_latency()*1000:6.1f}мс | "
            f"p95={self.p95_latency()*1000:6.1f}мс | "
            f"↓{recv_bps/1024:8.1f}КБ/с ↑{sent_bps/1024:8.1f}КБ/с | "
            f"коды: {codes or '-'}"
        )

    def summary(self) -> str:
        elapsed = max(1e-9, time.monotonic() - self.start_time)
        sent_bps, recv_bps = self.bytes_per_second
        codes = ", ".join(f"{k}:{v}" for k, v in sorted(self.status_codes.items()))
        return (
            f"Длительность: {elapsed:.1f} с\n"
            f"Всего запросов: {self.total}\n"
            f"Успешных: {self.ok}\n"
            f"Ошибок: {self.errors}\n"
            f"Средний RPS: {self.total / elapsed:.1f}\n"
            f"Средняя задержка: {self.avg_latency()*1000:.1f} мс\n"
            f"p95 задержка: {self.p95_latency()*1000:.1f} мс\n"
            f"Отправлено: {self.bytes_sent/1024/1024:.2f} МБ (↑{sent_bps/1024:.1f} КБ/с)\n"
            f"Получено: {self.bytes_received/1024/1024:.2f} МБ (↓{recv_bps/1024:.1f} КБ/с)\n"
            f"Коды ответов: {codes or '-'}"
        )


async def worker(session, url, method, stop_event, stats):
    while not stop_event.is_set():
        stats.record_request_sent()
        t0 = time.monotonic()
        status = None
        sent = len(method) + len(url) + 20
        received = 0
        try:
            async with session.request(
                method, url, timeout=aiohttp.ClientTimeout(total=15)
            ) as resp:
                body = await resp.read()
                status = resp.status
                received = len(body) + 200
        except asyncio.CancelledError:
            raise
        except Exception:
            status = None
        latency = time.monotonic() - t0
        stats.record_bytes(sent, received)
        stats.record_result(status, latency)


async def printer(stats, stop_event, interval=1.0):
    while not stop_event.is_set():
        await asyncio.sleep(interval)
        print(stats.report(), flush=True)


async def run(args):
    stop_event = asyncio.Event()

    ssl_ctx = None
    if args.insecure:
        ssl_ctx = ssl.create_default_context()
        ssl_ctx.check_hostname = False
        ssl_ctx.verify_mode = ssl.CERT_NONE

    connector = aiohttp.TCPConnector(
        limit=0, limit_per_host=0,
        ttl_dns_cache=300, enable_cleanup_closed=True, ssl=ssl_ctx,
    )
    headers = {"User-Agent": "loadtest/1.0 (own-site test)"}

    async with aiohttp.ClientSession(connector=connector, headers=headers) as session:
        stats = Stats(window_seconds=1.0)
        workers = []
        current_workers = max(1, int(args.rps))

        async def spawn(n):
            for _ in range(n):
                workers.append(asyncio.create_task(
                    worker(session, args.url, args.method, stop_event, stats)
                ))

        await spawn(current_workers)
        print(f"Старт: URL={args.url}  цель RPS={args.rps}  воркеров={current_workers}")
        print_task = asyncio.create_task(printer(stats, stop_event))

        async def tuner():
            nonlocal current_workers
            while not stop_event.is_set():
                await asyncio.sleep(1.0)
                actual = stats.packets_per_second
                if actual <= 0:
                    delta = max(1, current_workers // 2)
                else:
                    new_workers = int(current_workers * (args.rps / actual))
                    new_workers = max(1, min(new_workers, 5000))
                    delta = new_workers - current_workers
                if delta > 0:
                    await spawn(delta)
                    current_workers += delta
                elif delta < 0:
                    to_stop = min(-delta, len(workers))
                    for _ in range(to_stop):
                        w = workers.pop()
                        w.cancel()
                    current_workers -= to_stop

        tuner_task = asyncio.create_task(tuner())

        try:
            if args.duration > 0:
                await asyncio.sleep(args.duration)
                stop_event.set()
            else:
                while True:
                    await asyncio.sleep(0.5)
        except asyncio.CancelledError:
            pass
        finally:
            stop_event.set()
            for w in workers:
                w.cancel()
            await asyncio.gather(*workers, return_exceptions=True)
            tuner_task.cancel()
            print_task.cancel()
            await asyncio.gather(tuner_task, print_task, return_exceptions=True)
            print("\n=== Итог ===")
            print(stats.summary())


def main():
    parser = argparse.ArgumentParser(
        description="Асинхронный нагрузочный генератор. Только для СВОИХ серверов!"
    )
    parser.add_argument("--url", default="https://edu.gounn.ru/elk",
                        help="URL (по умолчанию http://y992103m.beget.tech)")
    parser.add_argument("--rps", type=float, default=10000,
                        help="Целевое число запросов (пакетов) в секунду")
    parser.add_argument("--duration", type=float, default=0,
                        help="Длительность в секундах (0 = бесконечно)")
    parser.add_argument("--method", default="GET", help="HTTP-метод")
    parser.add_argument("--insecure", action="store_true",
                        help="Игнорировать проверку TLS")
    args = parser.parse_args()

    try:
        asyncio.run(run(args))
    except KeyboardInterrupt:
        print("\nОстановлено пользователем.")


if __name__ == "__main__":
    main()