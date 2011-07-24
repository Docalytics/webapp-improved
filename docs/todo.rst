TODO: snippets to document
==========================

Common errors
-------------
- "TypeError: 'unicode' object is not callable": one possible reason is that
  the ``RequestHandler`` returned a string. If the handler returns anything, it
  **must** be a :class:`webapp2.Response` object. Or it must not return
  anything and write to the response instead using ``self.response.write()``.

Secret keys
-----------
Add a note about how to generate strong session secret keys::

    $ openssl genrsa -out ${PWD}/private_rsa_key.pem 2048

Jinja2 factory
--------------
To create Jinja2 with custom filters and global variables::

    from webapp2_extras import jinja2

    def jinja2_factory(app):
        j = jinja2.Jinja2(app)
        j.environment.filters.update({
            'my_filter': my_filter,
        })
        j.environment.globals.update({
            'my_global': my_global,
        })
        return j

    # When you need jinja, get it passing the factory.
    j = jinja2.get_jinja2(factory=jinja2_factory)

Configuration notes
-------------------
Notice that configuration is set primarily in the application. See:

    http://webapp-improved.appspot.com/guide/app.html#config

By convention, modules that are configurable in webapp2 use the module
name as key, to avpoid name clashes. Their configuration is then set in
a nested dict. So, e.g., i18n, jinja2 and sessions are configured like this::

    config = {}
    config['webapp2_extras.i18n'] = {
        'default_locale': ...,
    }
    config['webapp2_extras.jinja2'] = {
        'template_path': ...,
    }
    config['webapp2_extras.sessions'] = {
        'secret_key': ...,
    }
    app = webapp2.WSGIApplication(..., config=config)

You only need to set the configuration keys that differ from the default
ones. For convenience, configurable modules have a 'default_config'
variable just for the purpose of documenting the default values, e.g.:

    http://webapp-improved.appspot.com/api/extras.i18n.html#webapp2_extras.i18n.default_config
