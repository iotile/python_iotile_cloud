import sys
import logging
import argparse
import getpass

from iotile_cloud.api.connection import Api

logger = logging.getLogger(__name__)


class BaseMain(object):
    parser = None
    args = None
    api = None
    domain = 'https://iotile.cloud'

    def __init__(self):
        """
        Initialize Logging configuration
        Initialize argument parsing
        Process any extra arguments
        Only hard codes one required argument: --user
        Additional arguments can be configured by overwriting the add_extra_args() method
        Logging configuration can be changed by overwritting the config_logging() method
        """
        self.config_logging()
        self.parser = argparse.ArgumentParser(description=__doc__)
        self.parser.add_argument('-u', '--user', dest='email', type=str, help='Email used for login')

        self.add_extra_args()

        self.args = self.parser.parse_args()

        if not self.args.email:
            logger.error('User email is required: --user')
            sys.exit(1)

    def _critical_exit(self, msg):
        logger.error(msg)
        sys.exit(1)

    def main(self):
        """
        Main function to call to initiate execution.
        1. Get domain name and use to instantiate Api object
        2. Call before_login to allow for work before logging in
        3. Logging into the server
        4. Call after_loging to do actual work with server data
        5. Logout
        6. Call after_logout to do work at end of script
        :return: Nothing
        """
        self.domain = self.get_domain()
        self.api = Api(self.domain)
        self.before_login()
        ok = self.login()
        if ok:
            self.after_login()
            self.logout()
            self.after_logout()

    # Following functions can be overwritten if needed
    # ================================================

    def config_logging(self):
        """
        Overwrite to change the way the logging package is configured
        :return: Nothing
        """
        logging.basicConfig(level=logging.INFO,
                            format='[%(asctime)-15s] %(levelname)-6s %(message)s',
                            datefmt='%d/%b/%Y %H:%M:%S')

    def add_extra_args(self):
        """
        Overwrite to change the way extra arguments are added to the args parser
        :return: Nothing
        """
        pass

    def get_domain(self):
        """
        Overwrite to change the default domain
        :return: URL for server. e.g. 'https://iotile.cloud'
        """
        return self.domain

    def login(self):
        """
        Overwrite to change how to login to the server
        :return: True if successful
        """
        password = getpass.getpass()
        ok = self.api.login(email=self.args.email, password=password)
        return ok

    def logout(self):
        """
        Overwrite to change how to logout from server
        :return: Nothing
        """
        self.api.logout()

    def before_login(self):
        """
        Overwrite to do work after parsing, but before logging in to the server
        This is a good place to do additional custom argument checks
        :return: Nothing
        """
        pass

    def after_login(self):
        """
        This function MUST be overwritten to do actual work after logging into the Server
        :return: Nothing
        """
        logger.warning('No actual work done')

    def after_logout(self):
        """
        Overwrite if you want to do work after loging out of the server
        :return: Nothing
        """
        pass