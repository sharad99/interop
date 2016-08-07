"""Interoperability Prober.

Uses Interoperability Client and implementations of DataGenerator interface to
probe the interoperability server with requests. This can be used to
continuously validate the server is available to teams.
"""

import argparse
import datetime
import logging
import signal
import sys
import time

import datagen
import flightsim
from interop import AsyncClient, InteropError, Telemetry, StationaryObstacle, MovingObstacle


def run(client, data_generator, interop_time, logger):
    """Executes interoperability using the given configuration.

    Args:
        client: The interop client.
        data_generator: The generator of UAS telemetry.
        interop_time: The time between interoperability execution.
        logger: The logger to write status to.
    """
    # Continually execute interop requests until signaled to stop
    while True:
        # Get start time of the round
        start_time = datetime.datetime.now()
        # Get generated data
        telemetry = data_generator.get_uas_telemetry(start_time)
        # Execute interop requests
        telemetry_resp = client.post_telemetry(telemetry)
        obstacle_resp = client.get_obstacles()
        # Wait for completion
        telemetry_resp.result()
        obstacle_resp.result()
        # Note elapsed time
        end_time = datetime.datetime.now()
        elapsed_time = (end_time - start_time).total_seconds()
        logging.info('Executed interop. Total latency: %f', elapsed_time)
        # Delay for interop timing
        delay_time = interop_time - elapsed_time
        if delay_time > 0:
            try:
                time.sleep(delay_time)
            except KeyboardInterrupt:
                sys.exit(0)


def main():
    """Configures the interoperability binary."""
    # Setup logging
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    stream = logging.StreamHandler(sys.stdout)
    stream.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        '%(asctime)s. %(name)s. %(levelname)s. %(message)s')
    stream.setFormatter(formatter)
    logger.addHandler(stream)

    # Get parameters from command line
    parser = argparse.ArgumentParser(description='Interoperability prober.')
    parser.add_argument(
        'interop_server_host',
        type=str,
        help='Host and port of interoperability server. E.g. localhost:80')
    parser.add_argument(
        'interop_time',
        type=float,
        help='Time between interoperability request sets. Floating point '
        'seconds.')
    parser.add_argument('username',
                        type=str,
                        help='Username for interoperability login.')
    parser.add_argument('password',
                        type=str,
                        help='Password for interoperability login.')
    parser.add_argument('generator',
                        type=str,
                        choices=['zeros', 'flightsim'],
                        help='Data generation implementation.')
    parser.add_argument('flightsim_kml_path',
                        nargs='?',
                        type=str,
                        help='Path to the KML file for flightsim generation.')
    args = parser.parse_args()

    logging.info('Interop host: %s.', args.interop_server_host)
    logging.info('Interop time: %f.', args.interop_time)
    logging.info('Interop username: %s', args.username)
    logging.info('Generator: %s', args.generator)

    # Create client and data generator from parameters
    client = AsyncClient(args.interop_server_host, args.username,
                         args.password)
    if args.generator == 'zeros':
        data_generator = datagen.ZeroValueGenerator()
    else:
        data_generator = flightsim.KmlGenerator(args.flightsim_kml_path)

    # Launch prober
    run(client, data_generator, args.interop_time, logger)


if __name__ == '__main__':
    main()
