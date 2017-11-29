class MdoHelper(object):
    _m = 1
    _d = 1
    _o = None

    def __init__(self, m, d, o=None):
        self._m = m
        self._d = d
        self._o = o
        assert(isinstance(self._m, int ) and self._m != 0)
        assert(isinstance(self._d, int ) and self._d != 0)
        assert(self._o is None or isinstance(self._o, int ) or isinstance(self._o, float ))

    def compute(self, value):
        ret_value = 0.0
        if self._o:
            ret_value += self._o
        ret_value += (value * self._m / self._d)
        return ret_value

    def compute_reverse(self, value):
        ret_value = float(value)
        if self._o:
            ret_value -= self._o
        ret_value = (ret_value * self._d / self._m)
        return ret_value

    def __str__(self):
        result = ''
        if self._o:
            result += '{}+'.format(self._o)
        result += '{0}x/{1}'.format(self._m, self._d)
        return result