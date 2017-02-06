import sys
import json
import logging
import dateutil.parser

from ..api.connection import Api

logger = logging.getLogger(__name__)

class StreamData(object):
    data = []
    stream_id = None
    api = None

    def __init__(self, stream_id, api):
        self.stream_id = stream_id
        self.api = api

    def _get_args_dict(self, page, start=None, end=None, lastn=None):
        parts = {}
        parts['page'] = page
        if start:
            parts['start']='{0}'.format(start)
        if end:
            parts['end']='{0}'.format(end)
        if lastn:
            parts['lastn']='{0}'.format(lastn)
        return parts

    def _date_format(self, timestamp):
        try:
            dt = dateutil.parser.parse(timestamp)
            return dt
        except Exception as e:
            logger.error('Unable to parse timestamp (with parser): ' + str(e))
            sys.exit(1)

    def initialize_from_server(self, start=None, end=None, lastn=None):
        logger.info('Downloading data for {0}'.format(self.stream_id))
        page = 1
        while page:
            extra = self._get_args_dict(start=start, end=end, lastn=lastn, page=page)
            logger.debug('{0} ===> Downloading: {1}'.format(page, extra))
            raw_data = self.api.stream(self.stream_id).data.get(**extra)
            for item in raw_data['results']:
                if not item['display_value']:
                    item['display_value'] = 0
                self.data.append({
                    'timestamp': self._date_format(item['timestamp']),
                    'value': item['display_value']
                })
            if raw_data['next']:
                logger.debug('Getting more: {0}'.format(raw_data['next']))
                page += 1
            else:
                page = 0

        logger.info('==================================')
        logger.info('Downloaded a total of {0} records'.format(len(self.data)))
        logger.info('==================================')
