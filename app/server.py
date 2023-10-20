import argparse
import asyncio
import logging
import logging.config

import prometheus_client
from prometheus_client import start_http_server, Summary, Counter

import ping

logger = logging.getLogger("root")

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
    for retry in range(5):
        if retry != 0:
            logger.warning(f"Retrying {retry}")
            await asyncio.sleep(retry)
        aws = [asyncio.create_task(ping.ping(host, record, ping_interval), name=host) for host in hosts]
        done, pending = await asyncio.wait(aws, return_when=asyncio.FIRST_COMPLETED)
        logger.error(f"Tasks failed: {[task.get_name() for task in done]}")
        for task in pending:
            logger.warning(f"Cancelling {task.get_name()}")
            task.cancel()



if __name__ == "__main__":
    args = parse_args()
    asyncio.run(start(args.host, args.ping_interval))
