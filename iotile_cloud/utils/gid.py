
int16gid = lambda n: '-'.join(['{:04x}'.format(n >> (i << 4) & 0xFFFF) for i in range(0, 1)[::-1]])
int32gid = lambda n: '-'.join(['{:04x}'.format(n >> (i << 4) & 0xFFFF) for i in range(0, 2)[::-1]])
int48gid = lambda n: '-'.join(['{:04x}'.format(n >> (i << 4) & 0xFFFF) for i in range(0, 3)[::-1]])
int64gid = lambda n: '-'.join(['{:04x}'.format(n >> (i << 4) & 0xFFFF) for i in range(0, 4)[::-1]])

int2did = lambda n: int48gid(n)
int2pid = lambda n: int32gid(n)
int2vid = lambda n: int16gid(n)
int2bid = lambda n: int16gid(n)

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
    return int(hex_value, 16)


class IOTileCloudSlug(object):
    _slug = None

    def __str__(self):
        return self._slug

    def formatted_id(self):
        parts = gid_split(self._slug)
        return gid_join(parts[1:])

    def set_from_single_id_slug(self, type, terms, id):
        assert(type in ['p', 'd', 'b'])
        assert (isinstance(id, str))
        parts = gid_split(id)
        if parts[0] in ['p', 'd', 'b']:
            id = parts[1]
        id = fix_gid(id, terms)
        self._slug = gid_join([type, id])

    def get_id(self):
        parts = gid_split(self._slug)
        assert(len(parts) == 2)
        assert(parts[0] in ['p', 'd'])
        return gid2int(parts[1])


class IOTileProjectSlug(IOTileCloudSlug):
    """Formatted Global Project ID: p--0000-0001"""

    def __init__(self, id):
        if isinstance(id, int):
            pid = int2pid(id)
        else:
            pid = id
        self.set_from_single_id_slug('p', 2, pid)


class IOTileDeviceSlug(IOTileCloudSlug):
    """Formatted Global Device ID: d--0000-0000-0000-0001"""

    def __init__(self, id):
        if isinstance(id, int):
            did = int2did(id)
        else:
            did = id
        self.set_from_single_id_slug('d', 4, did)


class IOTileBlockSlug(IOTileCloudSlug):
    """Formatted Global DataBlock ID: b--0001-0000-0000-0001"""
    _block = None

    def __init__(self, id, block=0):
        if isinstance(id, int):
            did = int2did(id)
        else:
            parts = gid_split(id)
            if(len(parts) == 1):
                parts = ['d',] + parts
            assert(parts[0] in ['d', 'b'])
            id_parts = parts[1].split('-')
            if parts[0] == 'b':
                assert(len(id_parts) == 4)
                self._slug = id
                self._block = id_parts[0]
                return
            if len(id_parts) == 4:
                self._block = id_parts[0]
                did = '-'.join(id_parts[1:])
            else:
                assert(parts[0] == 'd')
                did = '-'.join(id_parts[0:])
        did = fix_gid(did, 3)
        if not self._block:
            self._block = int2bid(block)
        self.set_from_single_id_slug('b', 4, '-'.join([self._block, did]))

    def get_id(self):
        # DataBlocks should behave like Devices
        # get_id returns the device ID
        parts = gid_split(self._slug)
        assert(len(parts) == 2)
        id_parts = parts[1].split('-')
        hex_value = ''.join(id_parts[1:])
        return int(hex_value, 16)

    def get_block(self):
        return gid2int(self._block)


class IOTileVariableSlug(IOTileCloudSlug):
    """Formatted Global Variable ID: v--0000-0001--5000"""

    # Store local variable ID on top of globally unique slug
    _local = None

    def __init__(self, id, project=None):
        """

        :param id: Variable Local Id (string or int)
        :param project: IOTileCProjectSlug instance
        """
        if project:
            assert(isinstance(project, IOTileProjectSlug))
        if isinstance(id, int) and project != None:
            vid = int2vid(id)
            self._slug = gid_join(['v', project.formatted_id(), vid])
        else:
            assert (isinstance(id, str))
            parts = gid_split(id)
            if len(parts) == 1 and project != None:
                self._slug = gid_join(['v', project.formatted_id(), id])
            else:
                assert(project == None)
                assert(len(parts) == 3)
                self._slug = id
        self._local = gid_split(self._slug)[2]

    def formatted_local_id(self):
        return self._local


class IOTileStreamSlug(IOTileCloudSlug):

    def __init__(self, id=None):
        if id:
            assert(isinstance(id, str))
            assert(len(gid_split(id)) == 4)
            self._slug = id

    def from_parts(self, project, device, variable):
        if not isinstance(project, IOTileProjectSlug):
            project = IOTileProjectSlug(project)
        if not isinstance(device, IOTileDeviceSlug):
            device = IOTileDeviceSlug(device)
        if not isinstance(variable, IOTileVariableSlug):
            variable = IOTileVariableSlug(variable)
        self._slug = gid_join(['s', project.formatted_id(), device.formatted_id(), variable.formatted_local_id()])

    def get_parts(self):
        parts = gid_split(self._slug)
        assert(len(parts) == 4)
        project = IOTileProjectSlug(parts[1])
        device = IOTileDeviceSlug(parts[2])
        variable = IOTileVariableSlug(parts[3], project)
        result = {
            'project': str(project),
            'device': str(device),
            'variable': str(variable)
        }
        return result
