import logging

import json

from iotile_cloud.api.connection import Api
from iotile_cloud.utils.main import BaseMain

"""
The goal of this script is to build a configuration attribute for each line enabling us to know how the machines are disposed in the factory.
For a line, here "p--0000-01e9" (under the name ":report:factory:line:config"), the added configuration attribute should look like this:
"machines_layout": [
    {
            "type": "printer",
            "label": "Printer",
            "devices": [
                "d--0000-0000-0000-0d26"
            ],
            "sort": 1
        },
        {
            "type": "spi",
            "label": "SPI",
            "devices": [
                "d--0000-0000-0000-0d27"
            ],
            "sort": 2
        },
        {
            "type": "pnp",
            "label": "PnP",
            "devices": [
                "d--0000-0000-0000-0d28"
            ],
            "sort": 3
        },
        {
            "type": "oven",
            "label": "Oven",
            "devices": [
                "d--0000-0000-0000-0d29"
            ],
            "sort": 4
        },
        {
            "type": "aoi",
            "label": "AOI",
            "devices": [
                "d--0000-0000-0000-0d2a"
            ],
            "sort": 5
        }
]
For now, this script stores the result of all the configuration attributes that should be added in a JSON file.
You can run it using "support-flex" credentials to see all the config attributes in one JSON file, under their line slug.
"""

MACHINES_TYPES = {
    'laser': {
        'label': 'Laser',
        'sort': 0,
    },
    'printer': {
        'label': 'Printer',
        'sort': 1,
    },
    'spi': {
        'label': 'SPI',
        'sort': 2,
    },
    'pnp': {
        'label': 'PnP',
        'sort': 3,
    },
    'oven': {
        'label': 'Oven',
        'sort': 4,
    },
    'aoi': {
        'label': 'AOI',
        'sort': 5,
    },
    'glue': {
        'label': 'Glue',
        'sort': 6,
    },
}


def machine_type(machine):
    # Get the machine type and label from the above dictionnary. If it is not found, return "unknown"
    for key in MACHINES_TYPES.keys():
        if key in machine['label'].lower():
            return key
    return 'unknown'


logger = logging.getLogger(__name__)


class LineConfiguration(BaseMain):
    org_slug = 'flex'

    def after_login(self):
        # Get all lines
        lines = self.api.factory.line.get(org__slug=self.org_slug)

        machines_count = 0
        machines_layout = {}

        # For each lines, get the machines
        # A "real" line is identified with the fact that its "properties" are not empty
        for line in lines['results']:
            if line['properties']:
                machines_layout[line['slug']] = []
                machines = self.api.factory.machine.get(line=line['slug'])
                machines_count += machines['count']

                # For each machine of the line, get their type and build an object providing their label and their rank (sort) in the line
                for machine in machines['results']:
                    m_type = machine_type(machine)

                    #  There can be 2 machines of the same type in a line, take that into account
                    if m_type != 'unknown' and any(m['type'] == m_type for m in machines_layout[line['slug']]):
                        logger.info(
                            'Machines in parallel on line {0}'.format(line['slug']))
                        for m in machines_layout[line['slug']]:
                            if m['type'] == m_type:
                                m['devices'] += [machine['slug']]
                    else:
                        if m_type == 'unknown':
                            logger.warning(
                                'Unknown machine type on line {0}'.format(line['slug']))

                        # If the machine type is "unknown", use the real machine label and "-1" as its order in the line
                        machines_layout[line['slug']] += [{
                            'type': m_type,
                            'label': MACHINES_TYPES[m_type]['label'] if m_type != 'unknown' else machine['label'],
                            'devices': [machine['slug']],
                            'sort': MACHINES_TYPES[m_type]['sort'] if m_type != 'unknown' else -1
                        }]

        # Later, for each key of the "machines_layout" dictionnary, it will be possible here to update the config attribute with:
        #   - ":report:factory:line:config" as name
        #   - the dictionnary base keys (line slugs) as target
        #   - the dictionnay array corresponding to the base key as data

        logger.info('Number of lines found: {0}'.format(
            len(machines_layout.keys())))
        logger.info('Number of machines found: {0}'.format(machines_count))

        # Store the results in a JSON file
        with open('machines_layout.json', 'w') as file:
            json.dump(machines_layout, file)


if __name__ == '__main__':

    work = LineConfiguration()
    work.main()
