from builtins import int

int16gid = lambda n: '-'.join(['{:04x}'.format(n >> (i << 4) & 0xFFFF) for i in range(0, 1)[::-1]])
int32gid = lambda n: '-'.join(['{:04x}'.format(n >> (i << 4) & 0xFFFF) for i in range(0, 2)[::-1]])
int48gid = lambda n: '-'.join(['{:04x}'.format(n >> (i << 4) & 0xFFFF) for i in range(0, 3)[::-1]])
int64gid = lambda n: '-'.join(['{:04x}'.format(n >> (i << 4) & 0xFFFF) for i in range(0, 4)[::-1]])

int2did = lambda n: int48gid(n)
int2pid = lambda n: int32gid(n)
int2vid = lambda n: int16gid(n)
int2bid = lambda n: int16gid(n)
int2fid = lambda n: int48gid(n)

gid_split = lambda val: val.split('--')


def gid_join(elements):
    return '--'.join(elements)


def fix_gid(gid, num_terms):
    elements = gid.split('-')
    if len(elements) < num_terms:
        # Prepend '0000' as needed to get proper format (in groups of '0000')
        extras = ['0000' for i in range(num_terms - len(elements))]
        elements = extras + elements
    elif len(elements) > num_terms:
        # Only keep right most terms
        elements = elements[(len(elements) - num_terms):]

    return'-'.join(elements)


def gid2int(gid):
    elements = gid.split('-')
    hex_value = ''.join(elements)
    try:
        id = int(hex_value, 16)
    except Exception:
        raise ValueError('Expected HEX number. Got {}'.format(hex_value))
    return id


class IOTileCloudSlug(object):
    _slug = None

    def __str__(self):
        return self._slug

    def formatted_id(self):
        parts = gid_split(self._slug)
        return gid_join(parts[1:])

    def set_from_single_id_slug(self, type, terms, id):
        if type not in ['p', 'd', 'b', 'g']:
            raise ValueError('Slugs must start with p/d/b/g')
        if not isinstance(id, str):
            raise ValueError('Slug must be a string')
        parts = gid_split(id)
        if parts[0] in ['p', 'd', 'b', 'g']:
            id = parts[1]
        id = fix_gid(id, terms)
        self._slug = gid_join([type, id])

    def get_id(self):
        parts = gid_split(self._slug)
        if len(parts) != 2:
            raise ValueError('Cannot call get_id() for IDs with more than one term')
        if parts[0] not in ['p', 'd', 'g']:
            raise ValueError('Only Devices/DataBlocks/Fleets have single IDs')
        return gid2int(parts[1])


class IOTileProjectSlug(IOTileCloudSlug):
    """Formatted Global Project ID: p--0000-0001"""

    def __init__(self, id):
        if isinstance(id, int):
            if id < 0 or id >= pow(16, 8):
                raise ValueError('IOTileProjectSlug: UUID should be greater or equal than zero and less than 16^8')
            pid = int2pid(id)
        else:
            parts = gid_split(id)
            if len(parts) == 1:
                pid = parts[0]
            else:
                if parts[0] != 'p':
                    raise ValueError('IOTileProjectSlug: must start with a "p"')
                pid = gid_join(parts[1:])

            # Convert to int and back to get rid of anything above 48 bits
            id = gid2int(pid)
            if id < 0 or id >= pow(16, 8):
                raise ValueError('IOTileProjectSlug: UUID should be greater than zero and less than 16^8')
            pid = int2pid(id)

        self.set_from_single_id_slug('p', 2, pid)


class IOTileDeviceSlug(IOTileCloudSlug):
    """Formatted Global Device ID: d--0000-0000-0000-0001"""

    def __init__(self, id, allow_64bits=True):
        # For backwards compatibility, allow 64 bit IDs if required
        # Meaning that the device may in fact be a data block
        hex_count = 16 if allow_64bits else 12

        if isinstance(id, IOTileDeviceSlug):
            self._slug = id._slug
            return

        if isinstance(id, int):
            if id <= 0 or id >= pow(16, hex_count):
                raise ValueError('IOTileDeviceSlug: UUID should be greater than zero and less than 16^12')
            did = int2did(id)
        else:
            if not isinstance(id, str):
                raise ValueError('IOTileDeviceSlug: must be an int or str')
            parts = gid_split(id)
            if len(parts) == 1:
                did = parts[0]
            else:
                if parts[0] != 'd':
                    raise ValueError('IOTileDeviceSlug: must start with a "d"')
                did = gid_join(parts[1:])

            # Convert to int and back to get rid of anything above 48 bits
            id = gid2int(did)
            if id <= 0 or id >= pow(16, hex_count):
                raise ValueError('IOTileDeviceSlug: UUID should be greater than zero and less than 16^12')

        self.set_from_single_id_slug('d', 4, did)


class IOTileFleetSlug(IOTileCloudSlug):
    """Formatted Global Fleet ID: g--0000-0000-0001"""

    def __init__(self, id):
        if isinstance(id, int):
            if id < 0 or id >= pow(16, 12):
                raise ValueError('IOTileFleetSlug: UUID should be greater than zero and less than 16^12')
            fid = int2fid(id)
        else:
            if not isinstance(id, str):
                raise ValueError('IOTileFleetSlug: must be an int or str')
            parts = gid_split(id)
            if len(parts) == 1:
                fid = parts[0]
            else:
                if parts[0] != 'g':
                    raise ValueError('IOTileFleetSlug: must start with a "p"')
                fid = gid_join(parts[1:])

            # Convert to int and back to get rid of anything above 48 bits
            id = gid2int(fid)
            if id < 0 or id >= pow(16, 12):
                raise ValueError('IOTileFleetSlug: UUID should be greater than zero and less than 16^8')
            fid = int2fid(id)

        self.set_from_single_id_slug('g', 3, fid)


class IOTileBlockSlug(IOTileCloudSlug):
    """Formatted Global DataBlock ID: b--0001-0000-0000-0001"""
    _block = None

    def __init__(self, id, block=0):
        if isinstance(id, int):
            if id <= 0 or id >= pow(16, 16):
                raise ValueError('IOTileBlockSlug: UUID should be greater than zero and less than 16^16')
            did = int2did(id)
        else:
            parts = gid_split(id)
            if(len(parts) == 1):
                # gid2int will raise exception if not a proper HEX string
                id = gid2int(parts[0])
                if id <= 0 or id >= pow(16, 16):
                    raise ValueError('IOTileBlockSlug: UUID should be greater than zero')
                parts = ['d',] + parts
            if parts[0] not in ['d', 'b']:
                raise ValueError('IOTileBlockSlug: Slug must start with "b" or "d"')
            id_parts = parts[1].split('-')
            if parts[0] == 'b':
                if len(id_parts) != 4:
                    raise ValueError('IOTileBlockSlug: Expected format: b--xxxx-xxxx-xxxx-xxxx')
                self._slug = id
                self._block = id_parts[0]
                return
            if len(id_parts) == 4:
                self._block = id_parts[0]
                did = '-'.join(id_parts[1:])
            else:
                if parts[0] != 'd':
                    raise ValueError('DataBlock Slug must start with "b" or "d"')
                did = '-'.join(id_parts[0:])
        did = fix_gid(did, 3)
        if not self._block:
            self._block = int2bid(block)
        self.set_from_single_id_slug('b', 4, '-'.join([self._block, did]))


    def get_id(self):
        # DataBlocks should behave like Devices
        # get_id returns the device ID
        parts = gid_split(self._slug)
        if len(parts) != 2:
            raise ValueError('IOTileBlockSlug: Cannot call get_id() for IDs with more than one term')
        id_parts = parts[1].split('-')
        hex_value = ''.join(id_parts[1:])
        return int(hex_value, 16)

    def get_block(self):
        return gid2int(self._block)


class IOTileStreamerSlug(IOTileCloudSlug):
    """Formatted Global Streamer ID: t--0000-0000-0000-0000--0000.

    Args:
        device (str, int or IOTileDeviceSlug): The device that this streamer corresponds with.
        index (int): The sub-index of the stream in the device, typically a small number in [0, 8)
    """

    def __init__(self, device, index):
        if isinstance(device, int):
            device_id = device
        elif isinstance(device, IOTileDeviceSlug):
            device_id = device.get_id()
        elif isinstance(device, str):
            device_id = IOTileDeviceSlug(device).get_id()
        else:
            raise ValueError("IOTileStreamerSlug: Unknown device specifier, must be string, int or IOTileDeviceSlug")

        index = int(index)

        device_gid48 = int2did(device_id)
        index_gid = int16gid(index)
        device_gid = fix_gid(device_gid48, 4)

        self._slug = gid_join(['t', device_gid, index_gid])
        self._device = gid_join(['d', device_gid])
        self._index = index_gid

    def get_device(self):
        """Get the device slug as a string."""
        return self._device

    def get_index(self):
        """Get the streamer index in the device as a padded string."""
        return self._index


class IOTileVariableSlug(IOTileCloudSlug):
    """Formatted Global Variable ID: v--0000-0001--5000"""

    # Store local variable ID on top of globally unique slug
    _local = None

    def __init__(self, id, project=IOTileProjectSlug(0)):
        """

        :param id: Variable Local Id (string or int)
        :param project: IOTileCProjectSlug instance. Defaults to zero, which represent a wildcard
        """
        if project:
            if not isinstance(project, IOTileProjectSlug):
                project = IOTileProjectSlug(project)

        if isinstance(id, int):
            if id <= 0 or id >= pow(16, 4):
                raise ValueError('IOTileVariableSlug: UUID should be greater than zero')
            vid = int2vid(id)
            self._slug = gid_join(['v', project.formatted_id(), vid])
        else:
            if not isinstance(id, str):
                raise ValueError("IOTileVariableSlug: ID must be int or str")

            parts = gid_split(id)
            if len(parts) == 1:
                # gid2int will raise exception if not a proper HEX string
                gid2int(id)
                self._slug = gid_join(['v', project.formatted_id(), id])
            else:
                if len(parts) != 3:
                    raise ValueError("IOTileVariableSlug: Expected format: v--xxxx-xxxx--xxxx")
                self._slug = id
        self._local = gid_split(self._slug)[2]

    def formatted_local_id(self):
        return self._local


class IOTileStreamSlug(IOTileCloudSlug):

    def __init__(self, id=None):
        if id:
            if not isinstance(id, str):
                raise ValueError("Variable ID must be int or str")
            if len(gid_split(id)) != 4:
                raise ValueError("Stream slug must have three terms: s--<prj>--<dev>--<var>")
            self._slug = id

    def from_parts(self, project, device, variable):
        if not isinstance(project, IOTileProjectSlug):
            project = IOTileProjectSlug(project)
        if not isinstance(device, IOTileDeviceSlug):
            # Allow 64bits to handle blocks
            device = IOTileDeviceSlug(device, allow_64bits=True)
        if not isinstance(variable, IOTileVariableSlug):
            variable = IOTileVariableSlug(variable)
        self._slug = gid_join(['s', project.formatted_id(), device.formatted_id(), variable.formatted_local_id()])

    def get_parts(self):
        parts = gid_split(self._slug)
        assert(len(parts) == 4)
        project = IOTileProjectSlug(parts[1])
        device = IOTileDeviceSlug(parts[2], allow_64bits=True)
        variable = IOTileVariableSlug(parts[3], project)
        result = {
            'project': str(project),
            'device': str(device),
            'variable': str(variable)
        }
        return result
