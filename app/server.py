import argparse
import asyncio
import logging.config

import prometheus_client
from prometheus_client import start_http_server, Summary, Counter

import ping

LATENCY = prometheus_client.Summary(
    "ping_latency",
    "latency in milliseconds",
    ["host"],
)

SENT = prometheus_client.Counter("ping_sent", "total number of pings sent", ["host"])
DROPPED = prometheus_client.Counter(
    "ping_dropped", "total number of pings dropped", ["host"]
)

prometheus_client.REGISTRY.unregister(prometheus_client.GC_COLLECTOR)
prometheus_client.REGISTRY.unregister(prometheus_client.PLATFORM_COLLECTOR)
prometheus_client.REGISTRY.unregister(prometheus_client.PROCESS_COLLECTOR)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("host", type=str, nargs="+")
    parser.add_argument(
        "--ping-interval",
        "-p",
        type=float,
        default=5,
        help="How many seconds apart should each ping to a server be?",
    )
    parser.add_argument("--logging-config", type=str, default="logging.conf")
    args = parser.parse_args()

    logging.config.fileConfig(args.logging_config)
    return args


def record(host: str, lat: float | None) -> None:
    SENT.labels(host=host).inc()
    if lat is None:
        DROPPED.labels(host=host).inc()
    else:
        LATENCY.labels(host=host).observe(lat)


async def start(hosts: list[str], ping_interval: float):
    prometheus_client.start_http_server(5000)

    for host in hosts:
        SENT.labels(host=host)
        DROPPED.labels(host=host)
        LATENCY.labels(host=host)
        asyncio.ensure_future(ping.ping(host, record, ping_interval))

    while True:
        await asyncio.sleep(3600)


if __name__ == "__main__":
    args = parse_args()
    asyncio.run(start(args.host, args.ping_interval))
