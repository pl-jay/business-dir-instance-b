# apps/directory/templatetags/querystring.py
from django import template

register = template.Library()

@register.simple_tag(takes_context=True)
def querystring(context, **updates):
    """
    Usage:
      href="?{% querystring page=3 %}"
      href="?{% querystring page=page_obj.next_page_number sort='name' %}"
      href="?{% querystring page=None %}"  # remove key
    """

    print('AB')
    request = context["request"]
    params = request.GET.copy()
    for k, v in updates.items():
        if v is None:
            params.pop(k, None)
        else:
            params[k] = v
    return params.urlencode()
