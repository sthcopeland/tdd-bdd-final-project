"""Extra coverage for service.common.error_handlers"""
# pylint: disable=missing-class-docstring,too-few-public-methods

import json
import unittest

from service import app
from service.common import status
from service.models import DataValidationError


class TestErrorHandlersExtra(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.testing = True
        # Register throw routes once to avoid duplicate rule errors
        if not app.config.get("EXTRA_ERROR_ROUTES"):
            def raise_bad_request():
                from flask import abort
                abort(status.HTTP_400_BAD_REQUEST, "oops bad input")

            def raise_media_type():
                from werkzeug.exceptions import UnsupportedMediaType
                raise UnsupportedMediaType(description="nope")

            def raise_method_not_allowed():
                from werkzeug.exceptions import MethodNotAllowed
                raise MethodNotAllowed(valid_methods=["GET"])

            def raise_not_found():
                from werkzeug.exceptions import NotFound
                raise NotFound(description="gone")

            def raise_internal():
                raise RuntimeError("boom")

            def raise_dve():
                raise DataValidationError("bad data")

            app.add_url_rule("/_err/400", "raise_bad_request",
                             raise_bad_request, methods=["GET"])
            app.add_url_rule("/_err/415", "raise_media_type",
                             raise_media_type, methods=["GET"])
            app.add_url_rule("/_err/405", "raise_mna",
                             raise_method_not_allowed, methods=["GET"])
            app.add_url_rule("/_err/404", "raise_nf",
                             raise_not_found, methods=["GET"])
            app.add_url_rule("/_err/500", "raise_internal",
                             raise_internal, methods=["GET"])
            app.add_url_rule("/_err/dve", "raise_dve",
                             raise_dve, methods=["GET"])
            app.config["EXTRA_ERROR_ROUTES"] = True

    def setUp(self):
        self.client = app.test_client()

    def _assert_json(self, resp, code, label):
        self.assertEqual(resp.status_code, code)
        data = json.loads(resp.data)
        self.assertEqual(data["status"], code)
        self.assertEqual(data["error"], label)
        self.assertIn("message", data)
        self.assertIn("path", data)
        return data

    def test_bad_request(self):
        resp = self.client.get("/_err/400")
        self._assert_json(resp, status.HTTP_400_BAD_REQUEST, "Bad Request")

    def test_unsupported_media_type(self):
        resp = self.client.get("/_err/415")
        self._assert_json(
            resp, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, "Unsupported Media Type"
        )

    def test_method_not_allowed(self):
        resp = self.client.get("/_err/405")
        self._assert_json(
            resp, status.HTTP_405_METHOD_NOT_ALLOWED, "Method Not Allowed"
        )

    def test_not_found(self):
        resp = self.client.get("/_err/404")
        self._assert_json(resp, status.HTTP_404_NOT_FOUND, "Not Found")

    def test_internal_server_error(self):
        resp = self.client.get("/_err/500")
        self._assert_json(
            resp,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "Internal Server Error",
        )

    def test_data_validation_error(self):
        resp = self.client.get("/_err/dve")
        payload = self._assert_json(
            resp, status.HTTP_400_BAD_REQUEST, "Bad Request"
        )
        self.assertIn("bad data", payload["message"])
