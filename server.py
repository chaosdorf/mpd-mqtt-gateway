#!/usr/bin/env python3
import signal
import os
import logging
import argparse
import pathlib
import typing
import raven
from gateway import MpdServer, MqttServer, MpdMqttGateway

def setup_logging() -> None:
    logging.basicConfig(
        format="%(asctime)s:%(levelname)s:%(threadName)s:%(name)s:%(message)s",
        level=logging.INFO
    )


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Push mpd music metadata to mqtt")
    parser.add_argument("--mpd-hostname", required=True)
    parser.add_argument("--mpd-port", default=6600)
    parser.add_argument("--mqtt-hostname", required=True)
    parser.add_argument("--mqtt-port", default=1883)
    parser.add_argument("--mqtt-topic", default="music")
    args = parser.parse_args()
    return args


def setup_sentry() -> typing.Optional[raven.Client]:
    dsn_secret_path = pathlib.Path("/run/secrets/SENTRY_DSN")
    if dsn_secret_path.exists():
        dsn = dsn_secret_path.read_text().strip()
    elif "SENTRY_DSN" in os.environ:
        dsn = os.environ["SENTRY_DSN"]
    else:
        logging.warn("Didn't connect to Sentry because SENTRY_DSN is not set.")
        return None
    logging.info("Connecting to Sentry: %s", dsn)
    raven = raven.Client(dsn)
    logging.info("Connected to Sentry.")
    return raven


def create_gateway(args: argparse.Namespace) -> MpdMqttGateway:
    return MpdMqttGateway(
        mpd_server=MpdServer(
            hostname=args.mpd_hostname,
            port=args.mpd_port,
            timeout=5
        ),
        mqtt_server=MqttServer(
            hostname=args.mqtt_hostname,
            port=args.mqtt_port,
            timeout=5
        ),
        mqtt_topic=args.mqtt_topic
    )


if __name__ == "__main__":
    setup_logging()
    sentry = setup_sentry()
    try:
        args = parse_arguments()
        gateway = create_gateway(args)
        def shutdown_gateway(signum: int, frame: typing.Any) -> None:
            logging.info("Received %s", signal.Signals(signum).name)
            gateway.shutdown()
        signal.signal(signal.SIGINT, shutdown_gateway)
        signal.signal(signal.SIGTERM, shutdown_gateway)
        gateway.run()
    except Exception as exc:
        if sentry:
            sentry.captureException()
        raise
