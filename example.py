import getpass
import datetime
import logging
from pprint import pprint
from pystrato.connection import Api as StratoApi

from logging import StreamHandler, Formatter

logger = logging.getLogger(__name__)
FORMAT = '[%(asctime)-15s] %(levelname)-6s %(message)s'
DATE_FORMAT = '%d/%b/%Y %H:%M:%S'
formatter = Formatter(fmt=FORMAT, datefmt=DATE_FORMAT)
handler = StreamHandler()
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)

email = input('Email? ')
password = getpass.getpass()

c = StratoApi()

ok = c.login(email=email, password=password)
if ok:

    # GET Data
    my_organizations = c.org.get()
    for org in my_organizations['results']:
        logger.info('I am a member of {0}'.format(org['name']))
        org_projects = c.project.get(extra='org__slug={0}'.format(org['slug']))
        for proj in org_projects['results']:
            logger.info(' --> Project: {0}'.format(proj['name']))

        logger.info('------------------------------')

    # POST Data Stream
    # First, get a valid stream
    proj_id = 'e2c434d5-9ef9-497b-8670-5592078e5a8f'
    proj = c.project(proj_id).get()
    if proj:
        streams = c.stream.get(extra='project={0}'.format(proj['id']))
        # Get first one
        if streams['count']:
            stream = streams['results'][0]

            # Get last entry
            last_data = c.stream(stream['id'], action='data').get(extra='lastn=1')
            pprint(last_data['results'])

            # Post new data
            if last_data['count']:
                dt = datetime.datetime.utcnow()
                payload = {
                    'streamid': last_data['results'][0]['streamid'],
                    'timestamp': dt.isoformat(),
                    'value': 10
                }

                resp = c.stream(action='new_data').post(data=payload)
                logger.info('Created new data entry: {0}'.format(resp['id']))

        logger.info('------------------------------')

    c.logout()
