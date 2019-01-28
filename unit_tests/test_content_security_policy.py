import json
import unittest
from unittest import mock
from conveyancer_ui.main import app
from conveyancer_ui.custom_extensions.content_security_policy.main import ContentSecurityPolicy


class TestContentSecurityPolicy(unittest.TestCase):

    def setup_method(self, method):
        self.app = app.test_client()

    @mock.patch('conveyancer_ui.custom_extensions.content_security_policy.main.ContentSecurityPolicy.init_app')
    def test_extension_alternative_init(self, mock_init_app):
        ContentSecurityPolicy('foo')
        mock_init_app.assert_called_once_with('foo')

    def test_reporting_mode(self):
        app.config['CONTENT_SECURITY_POLICY_MODE'] = 'report-only'

        response = self.app.get('/')
        assert 'script-src' in response.headers['Content-Security-Policy-Report-Only']

    def test_full_mode(self):
        app.config['CONTENT_SECURITY_POLICY_MODE'] = 'full'

        response = self.app.get('/')
        assert 'script-src' in response.headers['Content-Security-Policy']

    @mock.patch('conveyancer_ui.custom_extensions.content_security_policy.reporting.logger.error')
    def test_report_route(self, mock_logger):
        response = self.app.post('/content-security-policy-report/?trace_id=Hello',
                                 data=json.dumps({'csp-report': {'foo': 'bar'}}),
                                 content_type='application/json')

        mock_logger.assert_called_once_with('CSP violation', extra={
            'content_security_policy_report': {'foo': 'bar'}
        })

        assert response.status_code == 204
