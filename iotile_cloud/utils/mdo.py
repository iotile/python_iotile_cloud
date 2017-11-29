class MdoHelper(object):
    _m = 1
    _d = 1
    _o = None

    def __init__(self, m, d, o=None):
        assert(isinstance(m, int ) and m != 0)
        assert(isinstance(d, int ) and d != 0)
        assert(o is None or isinstance(o, int ) or isinstance(o, float ))
        self._m = float(m)
        self._d = float(d)
        if o:
            self._o = float(o)

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