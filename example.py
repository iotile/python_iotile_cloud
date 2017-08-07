import getpass
import logging
import argparse
import sys

from iotile_cloud.api.connection import Api
from iotile_cloud.stream.data import StreamData, RawData
from iotile_cloud.api.exceptions import HttpNotFoundError

logging.basicConfig(level=logging.DEBUG,
                    format='[%(asctime)-15s] %(levelname)-6s %(message)s',
                    datefmt='%d/%b/%Y %H:%M:%S')

logger = logging.getLogger(__name__)

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('-u', '--user', dest='email', type=str, help='Email used for login')

parser.add_argument('-s', '--stream', dest='stream', type=str, help='Stream ID')

args = parser.parse_args()
logger.info('--------------')

if not args.email:
    logger.error('User email is required: --user')
    sys.exit(1)

password = getpass.getpass()

c = Api()

ok = c.login(email=args.email, password=password)
if ok:

    """
     Example for calling a GET: https://iotile.cloud/api/v1/org/
     And for each returned Organization, calling: https://iotile.cloud/api/v1/org/<slug>/projects/
     Other examples:
      all_my_projects = c.project.get()
      all_my_devices = c.device.get()
      all_my_streams = c.stream.get()
    """
    all_my_organizations = c.org.get()
    for org in all_my_organizations['results']:
        logger.info('I am a member of {0}'.format(org['name']))
        org_projects = c.org(org['slug']).projects.get()
        for proj in org_projects['results']:
            logger.info(' --> Project: {0}'.format(proj['name']))

    logger.info('------------------------------')

    """
    Example for using the StreamData class to query the last 10 data points for
    a given stream. For 10 items, this would be equivalent to just calling:
       stream_data = c.stream(args.stream).data.get(lastn=10)
    but StreamData is useful when getting more than 1K points, where you need
    to recursively fetch each page (1K at a time).
    """
    if args.stream:
        stream_data = StreamData(args.stream, c)
        try:
            stream_data.initialize_from_server(lastn=10)
        except HttpNotFoundError as e:
            logger.error(e)
        for item in stream_data.data:
            logger.info('{0}: {1}'.format(item['timestamp'], item['output_value']))

        logger.info('------------------------------')

    c.logout()
