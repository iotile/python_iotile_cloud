"""
Script to compute totals across multiple projects, devices and/or streams.

Usage:
- python report-generator-example.py -u user@test.com
                                     --t0 <start date> --t1 <end date>
                                     source [sources]

Examples:
- Generate report for September for project 1, project 2, device 0x111 and device 0x222:

    --t0 2017-09-01 --t1 2017-09-30 p--0001 p--0000-00002 d--1111 d--0000-0000-0000-2222

- Generate report for September for streams s--0000-0001--0000-0000-0000-1111--5001 and
  s--0000-0001--0000-0000-0000-1111--5002:

    --t0 2017-09-01 --t1 2017-09-30 s--0000-0001--0000-0000-0000-1111--5001 s--0000-0001--0000-0000-0000-1111--5002


"""
import sys
import argparse
import getpass
import logging
from pprint import pprint
from datetime import datetime
from dateutil.parser import parse as dt_parse

from iotile_cloud.api.connection import Api
from iotile_cloud.stream.report import AccumulationReportGenerator

PRODUCTION_DOMAIN_NAME = 'https://iotile.cloud'

logger = logging.getLogger(__name__)


if __name__ == '__main__':
    # Test
    # Logger Format
    logging.basicConfig(level=logging.DEBUG,
                        format='[%(asctime)-15s] %(levelname)-6s %(message)s',
                        datefmt='%d/%b/%Y %H:%M:%S')

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-u', '--user', dest='email', type=str, help='Email used for login')
    parser.add_argument('--t0', dest='t0', type=str, help='Start Date')
    parser.add_argument('--t1', dest='t1', type=str, help='End Date')

    parser.add_argument('sources', metavar='sources', nargs='+', type=str, help='Report source (projects, devices, streams)')

    args = parser.parse_args()
    logger.info('--------------')

    if not args.email:
        logger.error('User email is required: --user')
        sys.exit(1)

    if not args.t0:
        logger.error('Start Date is required: --t0')
        sys.exit(1)

    try:
        t0 = dt_parse(args.t0)
    except Exception as e:
        logger.error(e)
        sys.exit(1)

    if not args.t1:
        t1 = datetime.utcnow()
    else:
        try:
            t1 = dt_parse(args.t1)
        except Exception as e:
            logger.error(e)
            sys.exit(1)

    password = getpass.getpass()

    domain = PRODUCTION_DOMAIN_NAME

    logger.info('Using Server: {0}'.format(domain))
    c = Api(domain)

    ok = c.login(email=args.email, password=password)
    if ok:
        logger.info('Welcome {0}'.format(args.email))

        gen = AccumulationReportGenerator(c)
        stats =gen.compute_sum(sources=args.sources, start=t0, end=t1)

        pprint(stats)

        logger.info('Goodbye!!')
        c.logout()
