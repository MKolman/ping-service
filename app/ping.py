import re
import subprocess
import math
import datetime
import asyncio
import typing
import logging
from dataclasses import dataclass


logger = logging.getLogger("root")

float_fmt = r"\d+(\.\d+)?"
ip_fmt = r"\d{1,3}(\.\d{1,3}){3}"

ping_fmt = re.compile(
    rf"64 bytes from (?P<host>[0-9.a-z-]+)( \((?P<ip>{ip_fmt})\))?: icmp_seq=(?P<seq>\d+) ttl=(?P<ttl>\d+) time=(?P<time>{float_fmt}) ms\n"
)
dropped_fmt = re.compile(r"no answer yet for icmp_seq=(?P<seq>\d+)\n")
stats1_fmt = re.compile(
    rf"(?P<trans>\d+) packets transmitted, (?P<recv>\d+) received, (?P<loss>{float_fmt})% packet loss, time (?P<time>{float_fmt})ms\n"
)
stats2_fmt = re.compile(
    rf"rtt min/avg/max/mdev = (?P<min>{float_fmt})/(?P<avg>{float_fmt})/(?P<max>{float_fmt})/(?P<mdev>{float_fmt}) ms\n"
)


@dataclass
class PingEvent:
    seq: int
    latency_ms: typing.Optional[float]


def process_line(line_bytes: bytes) -> PingEvent | str | typing.Tuple:
    line = line_bytes.decode()
    if match := ping_fmt.fullmatch(line):
        group = match.groupdict()
        return PingEvent(int(group["seq"]), float(group["time"]))
    elif match := dropped_fmt.fullmatch(line):
        return PingEvent(int(match.groupdict()["seq"]), None)
    elif match := stats1_fmt.fullmatch(line):
        group = match.groupdict()
        return (int(group["trans"]), int(group["recv"]), float(group["loss"]))
    elif match := stats2_fmt.fullmatch(line):
        group = match.groupdict()
        return (
            float(group["min"]),
            float(group["avg"]),
            float(group["max"]),
            float(group["mdev"]),
        )
    else:
        return line.strip()


async def ping(
    host: str,
    out: typing.Callable[[str, float | None], None],
    interval: float,
) -> None:
    proc = await asyncio.create_subprocess_shell(
        " ".join(
            ["ping", "-W", f"{math.ceil(interval)}", "-i", f"{interval}", "-O", host]
        ),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    if proc.stdout is None:
        logger.error("Cannot attach to stdout of ping subprocess")
        return

    async for line in proc.stdout:
        data = process_line(line)
        if isinstance(data, PingEvent):
            out(host, data.latency_ms)
            logger.debug(data)
        else:
            logger.warn("Unprocessed line: %s", line.decode().strip())
