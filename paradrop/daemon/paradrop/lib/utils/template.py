import string


class TemplateFormatter(string.Formatter):
    """
    String formatter that supports method calls, loops, and conditionals.

    See: https://github.com/ebrehault/superformatter
    """

    def format_field(self, value, spec):
        if spec.startswith('repeat'):
            template = spec.partition(':')[-1]
            if type(value) is dict:
                value = value.items()
            return ''.join([template.format(item=item) for item in value])
        elif spec == 'call':
            return value()
        elif spec.startswith('if'):
            return (value and spec.partition(':')[-1]) or ''
        else:
            return super(TemplateFormatter, self).format_field(value, spec)
