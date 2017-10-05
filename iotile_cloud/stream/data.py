import sys
import json
import logging
import dateutil.parser

from ..api.connection import Api

logger = logging.getLogger(__name__)


class BaseData(object):
    data = []
    _api = None

    def __init__(self, api):
        self._api = api
        self.data = []

    def _get_args_dict(self, page, *args, **kwargs):
        parts = {}
        for key in kwargs.keys():
            parts[key] = kwargs[key]

        parts['page'] = page
        return parts

    def _date_format(self, timestamp):
        try:
            dt = dateutil.parser.parse(timestamp)
            return dt
        except Exception as e:
            logger.error('Unable to parse timestamp (with parser): ' + str(e))
            sys.exit(1)

    def _fetch_data(self, *args, **kwargs):
        logger.error('Fetch Data not implemented')
        return {}

    def initialize_from_server(self, *args, **kwargs):
        logger.debug('Downloading data')
        page = 1
        self.data = []
        while page:
            extra = self._get_args_dict(page=page, *args, **kwargs)
            logger.debug('{0} ===> Downloading data: {1}'.format(page, extra))
            raw_data = self._fetch_data(**extra)
            if 'results' in raw_data:
                for item in raw_data['results']:
                    self.data.append(item)
                if raw_data['next']:
                    logger.debug('Getting more: {0}'.format(raw_data['next']))
                    page += 1
                else:
                    page = 0

        logger.debug('==================================')
        logger.debug('Downloaded a total of {0} records'.format(len(self.data)))
        logger.debug('==================================')


class StreamData(BaseData):
    _stream_id = None

    def __init__(self, stream_id, api):
        super(StreamData, self).__init__(api)
        self._stream_id = stream_id

    def _fetch_data(self, *args, **kwargs):
        return self._api.stream(self._stream_id).data.get(**kwargs)


class RawData(BaseData):

    def __init__(self, api):
        super(RawData, self).__init__(api)

    def _fetch_data(self, *args, **kwargs):
        return self._api.data.get(**kwargs)
