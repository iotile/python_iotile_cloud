"""
Sample script to use IOTile Cloud
Main purpose of this example is to show how easy it is to use the Api class
The script first gets all organizations you have access to, and for each one, it gets all its projects.
It then uses the stream ID passed as an argument to get data for that stream

MyScript derives from BaseMain and overwrites the after_login function
The BaseMain will execute the following flow:

        # Create an argparse class (self.parser) and add default arguments, and then:
        self.add_extra_args()

        self.domain = self.get_domain()
        self.api = Api(self.domain)
        self.before_login()
        ok = self.login()
        if ok:
            self.after_login()
            self.logout()
            self.after_logout()

    See iotile_cloud/utils/main.py for additional details

"""
import logging

from iotile_cloud.api.connection import Api
from iotile_cloud.utils.main import BaseMain
from iotile_cloud.stream.data import StreamData
from iotile_cloud.api.exceptions import HttpNotFoundError

logger = logging.getLogger(__name__)


class MyScript(BaseMain):
    """
    It executed the following on its main function:

    So, we just have to overwrite the after_login function where we can write code to get data from server
    """

    def add_extra_args(self):
        # Add extra argument to take stream slug from user
        self.parser.add_argument('stream', metavar='stream', type=str,
                                 help='Stream Slug. e.g. s--0000-0001--0000-0000-0000-0001--5001')


    def after_login(self):
        """
         Example for calling a GET: https://iotile.cloud/api/v1/org/
         And for each returned Organization, calling: https://iotile.cloud/api/v1/org/<slug>/projects/
         Other examples:
          all_my_projects = c.project.get()
          all_my_devices = c.device.get()
          all_my_streams = c.stream.get()
        """
        all_my_organizations = self.api.org.get()
        for org in all_my_organizations['results']:
            logger.info('I am a member of {0}'.format(org['name']))
            org_projects = self.api.org(org['slug']).projects.get()
            for proj in org_projects['results']:
                logger.info(' --> Project: {0}'.format(proj['name']))

        logger.info('------------------------------')

        """
        Example for using the StreamData class to query the last 10 data points for
        a given stream. For 10 items, this would be equivalent to just calling:
           stream_data = api.stream(args.stream).data.get(lastn=10)
        but StreamData is useful when getting more than 1K points, where you need
        to recursively fetch each page (1K at a time).
        """
        if self.args.stream:
            stream_data = StreamData(self.args.stream, self.api)
            try:
                stream_data.initialize_from_server(lastn=10)
            except HttpNotFoundError as e:
                logger.error(e)
            for item in stream_data.data:
                logger.info('{0}: {1}'.format(item['timestamp'], item['output_value']))

            logger.info('------------------------------')


if __name__ == '__main__':

    work = MyScript()
    work.main()

