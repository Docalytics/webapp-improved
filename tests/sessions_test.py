# -*- coding: utf-8 -*-
import unittest

import webapp2
from webapp2_extras import sessions

import test_base

class App(object):
    @property
    def config(self):
        config = sessions.default_config.copy()
        config['secret_key'] = 'my-super-secret'
        return {'webapp2_extras.sessions': config}

app = App()


class TestSecureCookieSession(test_base.BaseTestCase):
    factory = sessions.SecureCookieSessionFactory

    def test_get_save_session(self):
        req = webapp2.Request.blank('/')
        req.app = app
        store = sessions.SessionStore(req)

        session = store.get_session(factory=self.factory)
        session['a'] = 'b'
        session['c'] = 'd'
        session['e'] = 'f'

        rsp = webapp2.Response()
        store.save_sessions(rsp)

        cookies = rsp.headers.get('Set-Cookie')
        req = webapp2.Request.blank('/', headers=[('Cookie', cookies)])
        req.app = app
        store = sessions.SessionStore(req)

        session = store.get_session(factory=self.factory)
        self.assertEqual(session['a'], 'b')
        self.assertEqual(session['c'], 'd')
        self.assertEqual(session['e'], 'f')


if __name__ == '__main__':
    test_base.main()
