import unittest

import requests_mock

from config import TestingConfig
from response_operations_ui import app


class TestCase(unittest.TestCase):

    def setUp(self):
        app_config = TestingConfig()
        app.config.from_object(app_config)
        app.login_manager.init_app(app)
        self.app = app.test_client()
        self.case_group_status = {
            "ru_ref": "19000001",
            "ru_name": "RU Name",
            "trading_as": "Company Name",
            "survey_id": "123",
            "short_name": "MYSURVEY",
            "current_status": "NOTSTARTED",
            "available_statuses": {
                "UPLOADED": "COMPLETE",
                "COMPLETED_BY_PHONE": "COMPLETEDBYPHONE"
            }
        }

    @requests_mock.mock()
    def test_get_available_status(self, mock_request):
        short_name = 'MYSURVEY'
        period = '221_202018'
        ru_ref = '19000001'
        mock_request.get(f'{app.config["BACKSTAGE_API_URL"]}/v1/case/status/{short_name}/{period}/{ru_ref}',
                         json=self.case_group_status)

        response = self.app.get(f'/case/{ru_ref}/change-response-status?survey={short_name}&period={period}')

        data = response.data
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'19000001', data)
        self.assertIn(b'RU Name', data)
        self.assertIn(b'Company Name', data)
        self.assertIn(b'123 &nbsp; MYSURVEY', data)
        self.assertIn(b'Not started', data)
        self.assertIn(b'Completed by phone', data)
        self.assertIn(b'Completed', data)

    @requests_mock.mock()
    def test_get_available_status_fail(self, mock_request):
        short_name = 'MYSURVEY'
        period = '221_202018'
        ru_ref = '19000001'
        mock_request.get(f'{app.config["BACKSTAGE_API_URL"]}/v1/case/status/{short_name}/{period}/{ru_ref}',
                         status_code=500)

        response = self.app.get(f'/case/{ru_ref}/change-response-status?survey={short_name}&period={period}',
                                follow_redirects=True)

        self.assertEqual(response.status_code, 500)
        self.assertIn("Error 500 - Server error".encode(), response.data)

    @requests_mock.mock()
    def test_should_update_status_completed_by_phone(self, mock_request):
        short_name = 'MYSURVEY'
        period = '221_202018'
        ru_ref = '19000001'

        mock_request.post(f'{app.config["BACKSTAGE_API_URL"]}/v1/case/status/'
                          f'{short_name}/{period}/{ru_ref}',
                          additional_matcher=lambda r: {'event': 'COMPLETEDBYPHONE'} == r.json())

        response = self.app.post(f'/case/{ru_ref}/change-response-status?survey={short_name}&period={period}',
                                 data={'event': 'COMPLETEDBYPHONE'})

        self.assertEqual(response.status_code, 302)
        self.assertIn('reporting-unit', response.location)

    @requests_mock.mock()
    def test_should_redirect_after_updating_status(self, mock_request):
        short_name = 'MYSURVEY'
        period = '221_202018'
        ru_ref = '19000001'

        mock_request.post(f'{app.config["BACKSTAGE_API_URL"]}/v1/case/status/'
                          f'{short_name}/{period}/{ru_ref}',
                          additional_matcher=lambda r: {'event': 'COMPLETEDBYPHONE'} == r.json())

        response = self.app.post(f'/case/{ru_ref}/change-response-status?survey={short_name}&period={period}',
                                 data={'event': 'COMPLETEDBYPHONE'})

        self.assertIn('reporting-unit', response.location)
        self.assertIn(f'survey={short_name}', response.location)
        self.assertIn(f'period={period}', response.location)

    @requests_mock.mock()
    def test_should_get_error_page_when_backstage_fails(self, mock_request):
        short_name = 'MYSURVEY'
        period = '221_202018'
        ru_ref = '19000001'
        mock_request.post(f'{app.config["BACKSTAGE_API_URL"]}/v1/case/status/'
                          f'{short_name}/{period}/{ru_ref}', status_code=503)

        response = self.app.post(f'/case/{ru_ref}/change-response-status?survey={short_name}&period={period}',
                                 data={'event': 'COMPLETEDBYPHONE'}, follow_redirects=True)

        self.assertEqual(response.status_code, 500)
        self.assertIn("Error 500 - Server error".encode(), response.data)

    @requests_mock.mock()
    def test_should_not_change_status_when_event_not_sent(self, mock_request):
        short_name = 'MYSURVEY'
        period = '221_202018'
        ru_ref = '19000001'
        mock_request.get(f'{app.config["BACKSTAGE_API_URL"]}/v1/case/status/{short_name}/{period}/{ru_ref}',
                         json=self.case_group_status)

        response = self.app.post(f'/case/{ru_ref}/change-response-status?survey={short_name}&period={period}')

        self.assertEqual(response.status_code, 200)
