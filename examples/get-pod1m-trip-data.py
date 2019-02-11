"""
Script to get all Trip Data uploaded from an Arch Systems POD-1M device.

The following describes the complete lifecycle of a POD-1M trip:

1. When the POD-1M receives a command to start a trip (from the Companion App), the device creates a new entry on its
   0e00 (Start Trip) stream. This represents the time at which the trip started.
2. The POD-1M will start recording both environmental data (5021, 5022, and 5023) and shock events (5020).
3. When the POD-1M receives a command to end the trip, the device creates a new entry on its 0e01 (End Trip) stream.
   This represents the time at which the trip ended.
4. All of this is so far on the device itself, but at some point after the trip is ended, the user will upload this data
   to the cloud using the Companion App, at which time, all of these streams will be populated with data.
5. The cloud is usually configured with a stream filter to send an email when the 0e01 signal is processed.
   A filter could be changed to instead call a webhook on another server.
6. After a device reviews the trip data on the cloud, the user is able to either reset the data (delete all the stream data/events)
   or archive the trip, in which case all the data is kept but the streams are changed to the one for a Data Block which is equivalent
   to a device (but read only). All the stream APIs work on either an active trip (device) or an archived trip (Data Block).
   At this point, the device itself can be cleared and a new trip can be started.

This script is intended to be used after step 5, which is when the trip was ended on the device and the data was uploaded to the cloud.

Run like:

     python3 -m venv  ~/.virtualenv/iotile-cloud
     pip install iotile-cloud
     python get_trip_data.py <device_slug>   # where device_slug can be `d--0abc` or `d--0000-0000-0000-0abc` just `0abc`

You must have access to that device (i.e. be a member of the Organization this device is claimed under) to access device data.

* For more, an introduction to the IOTile Cloud API can be found: https://drive.google.com/file/d/0B1p5WJhiz362ZWV5TUloWXNNU2c/view
* The official API reference can be found: https://iotile.cloud/api/docs
* Notes about the script:
   - Uncomment all pprint commands to learn what the different APIs are returning

"""
import logging
import sys
from pprint import pprint

from iotile_cloud.api.connection import Api
from iotile_cloud.utils.main import BaseMain
from iotile_cloud.stream.data import StreamData
from iotile_cloud.utils.gid import IOTileDeviceSlug, IOTileStreamSlug, IOTileProjectSlug, IOTileVariableSlug
from iotile_cloud.api.exceptions import HttpNotFoundError, HttpClientError
from iotile_cloud.utils.basic import datetime_to_str

logger = logging.getLogger(__name__)
TRIP_VARS = {
    'TRIP_START': '0e00',   # Timestamp represents the time the trip started
    'TRIP_END': '0e01',     # Timestamp represents the time the trip ended
    'TRIP_SUMMARY': '5a07', # This is an event that represents the optionally generated Trip Summary. It has basic trip information (Max G, diration, etc.)
    'SHOCK_EVENTS': '5020', # This is the stream that contains all shock events, with detailed waveforms
    'PRESSURE': '5021',     # This is the stream that contains the environmental "Pressure", captured every 15min
    'HUMIDITY': '5022',     # This is the stream that contains the environmental "Relative Humidity", captured every 15min
    'TEMPERATURE': '5023',  # This is the stream that contains the environmental "Temperature", captured every 15min
}


class TripData(BaseMain):
    """
    This Class derives from BaseMain and overwrites the required functions to change the arguments and do the actual work.
    The base class will store:
     - self.parser: The script argument parser
     - self.api: The IOTile Cloud Connection API. After login, use to get/post/patch/put/delete on any cloud resource (i.e. Rest API)
    """
    _project = None
    _device = None

    def add_extra_args(self):
        """
        Add extra argument to take
          - device slug from user

        :return: Nothing
        """
        self.parser.add_argument('device_slug', metavar='device_slug', type=str,
                                 help='Device Slug for the active Trip. e.g. d--0001')

    def _get_device_and_project(self):
        """
        Get the Device and Project Info, and stored

        :return: (Device, Project) objects
        """
        try:
            device_slug = IOTileDeviceSlug(self.args.device_slug)
        except ValueError as e:
            logger.error(e)
            return None, None

        try:
            device = self.api.device(str(device_slug)).get()
        except HttpNotFoundError:
            logger.error('Device not found: {}'.format(device_slug))
            sys.exit(1)

        if device:
            project_id = device['project']

            try:
                # Get the device information, mostly to get Sensor Graph and Project
                project = self.api.project(project_id).get()
            except HttpNotFoundError:
                logger.error('Project not found: {}'.format(project_id))
                sys.exit(1)

            return device, project

        return None, None

    def _get_stream_slug(self, var_id):
        """
        Form the stream slug given a variable ID (e.g. '5020')

        :param var_id: string representing hex variable id as a string
        :return: formed slug
        """
        assert self._device and self._project
        device_slug = IOTileDeviceSlug(self._device['slug'])
        project_slug = IOTileProjectSlug(self._project['slug'])
        stream_slug = IOTileStreamSlug()
        stream_slug.from_parts(project=project_slug, device=device_slug, variable=var_id)
        return stream_slug

    def _get_trip_range(self):
        """
         For the given trip, get the start and end timestamps

        :return: (string, string) representing start/end timestamps
        """
        start_data = self._get_last('data', self._get_stream_slug(TRIP_VARS['TRIP_START']))
        end_data = self._get_last('data', self._get_stream_slug(TRIP_VARS['TRIP_END']))

        # pprint(start_data)
        # pprint(end_data)

        if start_data and end_data:
            return start_data['timestamp'], end_data['timestamp']
        return None, None

    def _get_last(self, stream_type, stream_slug):
        """
        Get last data or event for given stream

        :param stream_type: 'data' or 'event'
        :param stream_slug: Stream Slug
        :return: Data or Event record
        """
        try:
            # Get the last data for the given stream
            if stream_type == 'data':
                data = self.api.data().get(filter=stream_slug, lastn=1)
            elif stream_type == 'event':
                data = self.api.event().get(filter=stream_slug, lastn=1)
            else:
                logger.error('Incorrect stream type')
                return None
        except HttpNotFoundError as e:
            logger.error(e)
            sys.exit(1)

        if data['count'] == 1:
            return data['results'][0]
        return None

    def _get_range(self, stream_type, stream_slug, start, end):
        """
        Get all data or events between the start and end timestamps

        :param stream_type: 'data' or 'event'
        :param stream_slug: Stream Slug
        :param start: Get all data with timestamp greater than or equal. e.g. `2019-02-09T00:01:03Z`
        :param end: Get all data with timestamp less than. e.g. `2019-02-09T00:01:03Z`
        :return: array of datas or events
        """
        try:
            if stream_type == 'data':
                # Get the stream data within this time range
                # Use the stream API (instead of the data API) to get the data value base on the output units
                data = self.api.stream(str(stream_slug)).data.get(start=start, end=end, page_size=5000)
            elif stream_type == 'event':
                data = self.api.event().get(filter=str(stream_slug), start=start, end=end, page_size=5000)
            else:
                logger.error('Incorrect stream type')
                return []
        except HttpNotFoundError as e:
            logger.error(e)
            sys.exit(1)

        if data['count'] > 0:
            return data['results']
        return []

    def after_login(self):
        """
        1.- Get Device Info
        2.- Get Project ID from Device and get Project Info
        3.- Given the device and project, we can contruct the required Stream slugs, and with them, get the actual data

        :return: Nothing
        """

        self._device, self._project = self._get_device_and_project()
        if self._device and self._project:
            # pprint(self._device)
            # pprint(self._project)

            start_ts, end_ts = self._get_trip_range()
            if start_ts and end_ts:
                logger.info('--------------------------------------------------------------------------')
                logger.info('Processing Trip: {} ({})'.format(self._device['label'], self._device['slug']))
                logger.info('Porcessing Trip from {} to {}'.format(start_ts, end_ts))
                logger.info('--------------------------------------------------------------------------')

                # First, get the last Trip Summary
                summary = self._get_last('event', self._get_stream_slug(TRIP_VARS['TRIP_SUMMARY']))
                if summary:
                    for key in summary['extra_data'].keys():
                        logger.info('--> {}: {}'.format(key, summary['extra_data'][key]))

                # Get environmental Data
                pressure_data = self._get_range('data', self._get_stream_slug(TRIP_VARS['PRESSURE']), start_ts, end_ts)
                humidity_data = self._get_range('data', self._get_stream_slug(TRIP_VARS['HUMIDITY']), start_ts, end_ts)
                temp_data = self._get_range('data', self._get_stream_slug(TRIP_VARS['TEMPERATURE']), start_ts, end_ts)

                logger.info('Got {} pressure data records'.format(len(pressure_data)))
                logger.info('Got {} relative humidity data records'.format(len(humidity_data)))
                logger.info('Got {} temperature data records'.format(len(temp_data)))
                # pprint(pressure_data[0])
                # pprint(humidity_data[0])
                # pprint(temp_data[0])

                # Get Shock Events
                shock_events = self._get_range('event', self._get_stream_slug(TRIP_VARS['SHOCK_EVENTS']),
                                               start_ts, end_ts)
                logger.info('Got {} shock event records'.format(len(shock_events)))
                # pprint(shock_events[0])

                # Find the worst case accelerometer G event, and download the detailed waveforms for it
                max_peak_event = None
                for event in shock_events:
                    if max_peak_event == None:
                        max_peak_event = event
                        continue
                    if event['extra_data']['peak'] > max_peak_event['extra_data']['peak']:
                        max_peak_event = event
                # Download event details (waveform) for max peak event
                max_peak_detailed_data = self.api.event(max_peak_event['id']).data.get()
                # pprint(max_peak_detailed_data)
                logger.info('Got max peak waveform with {} x, {} y and {} z points'.format(
                    len(max_peak_detailed_data['acceleration_data']['x']),
                    len(max_peak_detailed_data['acceleration_data']['y']),
                    len(max_peak_detailed_data['acceleration_data']['z'])
                ))
        else:
            logger.error('Device and/or Project not found or user has no access')


if __name__ == '__main__':
    work = TripData()
    work.main()
