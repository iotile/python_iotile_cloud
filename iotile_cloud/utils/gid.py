
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


class IOTileCloudSlug(object):
    _slug = None

    def __str__(self):
        return self._slug

    def formatted_id(self):
        parts = gid_split(self._slug)
        return gid_join(parts[1:])

    def set_from_single_id_slug(self, type, terms, id):
        assert(type in ['p', 'd'])
        assert (isinstance(id, str))
        parts = gid_split(id)
        if parts[0] in ['p', 'd']:
            id = parts[1]
        id = fix_gid(id, terms)
        self._slug = gid_join([type, id])


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
        assert(isinstance(project, IOTileProjectSlug))
        assert(isinstance(device, IOTileDeviceSlug))
        assert(isinstance(variable, IOTileVariableSlug))
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
