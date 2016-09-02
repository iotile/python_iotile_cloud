import getpass
import datetime
from pprint import pprint
from pystrato.connection import Api as StratoApi

email = input('Email? ')
password = getpass.getpass()

c = StratoApi()

ok = c.login(email=email, password=password)
if ok:

    # GET Data
    my_organizations = c.org.get()
    for org in my_organizations['results']:
        print('I am a member of {0}'.format(org['name']))
        org_projects = c.project.get(extra='org__slug={0}'.format(org['slug']))
        for proj in org_projects['results']:
            print(' --> Project: {0}'.format(proj['name']))

    print('------------------------------')

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
                print('Created new data entry: {0}'.format(resp['id']))

    print('------------------------------')

    c.logout()
