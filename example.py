import getpass
import logging
import argparse
import sys

from iotile_cloud.api.connection import Api
from iotile_cloud.stream.data import StreamData

from logging import StreamHandler, Formatter

logger = logging.getLogger(__name__)
FORMAT = '[%(asctime)-15s] %(levelname)-6s %(message)s'
DATE_FORMAT = '%d/%b/%Y %H:%M:%S'
formatter = Formatter(fmt=FORMAT, datefmt=DATE_FORMAT)
handler = StreamHandler()
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('-u', '--user', dest='email', type=str, help='Email used for login')

parser.add_argument('--id', dest='stream_id', type=str, help='ID of stream definition to get')
parser.add_argument('--lastn', dest='lastn', type=int, help='Number of Entries')

args = parser.parse_args()
logger.info('--------------')

if not args.email:
    logger.error('User email is required: --user')
    sys.exit(1)

password = getpass.getpass()

c = Api()

ok = c.login(email=args.email, password=password)
if ok:

    # GET Data
    my_organizations = c.org.get()
    for org in my_organizations['results']:
        logger.info('I am a member of {0}'.format(org['name']))
        org_projects = c.project.get(extra='org__slug={0}'.format(org['slug']))
        for proj in org_projects['results']:
            logger.info(' --> Project: {0}'.format(proj['name']))

    logger.info('------------------------------')

    if args.stream_id:
        stream_data = StreamData(args.stream_id, c)
        stream_data.initialize_from_server(lastn=100)
        for item in stream_data.data:
            logger.info('{0}: {1}'.format(item['timestamp'], item['value']))

        logger.info('------------------------------')

    c.logout()
