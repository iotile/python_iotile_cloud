import logging
from pprint import pprint
from datetime import datetime

from ..api.connection import Api
from ..api.exceptions import HttpNotFoundError, HttpClientError
from ..stream.data import StreamData
from ..utils.gid import *
from ..utils.basic import datetime_to_str

logger = logging.getLogger(__name__)

class BaseReportGenerator(object):
    _api = None
    _stream_slugs = []
    _streams = []

    def __init__(self, api):
        self._api = api
        self._clean()

    def _clean(self):
        self._stream_slugs = []
        self._streams = []

    def _add_streams(self, streams):

        # pprint.pprint(streams)
        logger.debug('Adding {} streams'.format(streams['count']))
        self._stream_slugs += [s['slug'] for s in streams['results']]
        self._streams += streams['results']

    def _fetch_streams_from_project_slug(self, slug):
        project_slug = IOTileProjectSlug(slug)
        try:
            streams = self._api.stream().get(project=str(project_slug))
            self._add_streams(streams)
        except HttpClientError as e:
            logger.warning(e)

    def _fetch_streams_from_device_slug(self, slug):
        device_slug = IOTileDeviceSlug(slug)

        try:
            streams = self._api.stream().get(device=str(device_slug))
            self._add_streams(streams)
        except HttpClientError as e:
            logger.warning(e)

    def _fetch_stream_from_slug(self, slug):
        stream_slug = IOTileStreamSlug(slug)

        try:
            stream = self._api.stream(str(stream_slug)).get()
            self._stream_slugs.append(stream['slug'])
            self._streams += [stream,]
        except HttpClientError as e:
            logger.warning(e)

    def _process_data(self, start, end=None):
        logger.error('_process_data must be implemented')
        return {}

    def compute_sum(self, sources, start, end=None):
        factory = {
            'p--': self._fetch_streams_from_project_slug,
            'd--': self._fetch_streams_from_device_slug,
            's--': self._fetch_stream_from_slug,
        }

        # Given the list of source slugs (project or device), get a unified list of devices
        self._clean()
        for src in sources:
            prefix = src[0:3]
            if prefix in factory:
                factory[prefix](src)
            else:
                logger.error('Illegal source slug: {}'.format(src))

        if len(self._streams):
            logger.info('Processing {} streams'.format(len(self._streams)))
            stats = self._process_data(start, end)
        else:
            msg = 'No streams were found for these GIDs'
            logger.error(msg)
            stats = { 'error': msg }

        return stats


class AccumulationReportGenerator(BaseReportGenerator):
    """
    For every stream, compute the total sum of its data
    Compute grand total across all streams
    """

    def __init__(self, api):
        super(AccumulationReportGenerator, self).__init__(api)

    def _process_data(self, start, end=None):
        logger.debug('Processing Data from {0} to {1}'.format(start, end))

        if end:
            end = datetime_to_str(end)
        else:
            end = datetime_to_str(datetime.utcnow())

        start = datetime_to_str(start)
        logger.debug('--> start={0}, end={1}'.format(start, end))

        stream_stats = {
            'streams': {},
            'total': 0
        }
        # pprint(self._streams)
        for stream in self._streams:
            stream_data = StreamData(stream['slug'], self._api)
            try:
                stream_data.initialize_from_server(start=start, end=end)
            except HttpNotFoundError as e:
                logger.error(e)

            sum = 0
            for item in stream_data.data:
                sum += item['output_value']

            if sum:
                stream_stats['streams'][stream['slug']] = {
                    'sum': sum,
                    'units': stream['output_unit']['unit_short']
                }
                stream_stats['total'] += sum

        return stream_stats
