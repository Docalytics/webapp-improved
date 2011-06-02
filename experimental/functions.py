# Helpers to work with view functions.
import urlparse

import webapp2


def uri_for(_name, *args, **kwargs):
    request = webapp2.get_request()
    return request.app.router.build(request, _name, args, kwargs)


def redirect(response, uri, permanent=False, abort=False):
    if uri.startswith(('.', '/')):
        uri = str(urlparse.urljoin(webapp2.get_request().url, uri))

    if permanent:
        code = 301
    else:
        code = 302

    if abort:
        webapp2.abort(code, headers=[('Location', uri)])

    response.headers['Location'] = uri
    response.set_status(code)
    response.clear()


def redirect_to(response, _name, _permanent=False, _abort=False, *args,
    **kwargs):
    uri = uri_for(_name, *args, **kwargs)
    redirect(response, uri, permanent=_permanent, abort=_abort)
