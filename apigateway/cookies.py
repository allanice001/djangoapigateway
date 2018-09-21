from http.cookies import Morsel


class StringMorsel(Morsel):
    def __init__(self, value):
        super(StringMorsel, self).__init__()
        self._value = value

    def output(self, attrs=None, header="Set-Cookie:"):
        return "%s %s" % (header, self.value)
