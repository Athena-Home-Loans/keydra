import unittest

from unittest.mock import patch
from unittest.mock import MagicMock

from requests import Response
from keydra.clients import qualys

CREDS = {
  "platform": "US3",
  "username": "user",
  "password": "pass",
  "rotatewith": "secrettwo"
}

XML_RESP_PWCHG = b'''<?xml version="1.0" encoding="UTF-8" ?>
<!DOCTYPE USER_LIST_OUTPUT SYSTEM
"https://qualysapi.qg3.apps.qualys.com/user_list_output.dtd">
<PASSWORD_CHANGE_OUTPUT>
  <RETURN><CHANGES><USER_LIST><USER><PASSWORD>Password123
  </PASSWORD></USER></USER_LIST></CHANGES></RETURN>
</PASSWORD_CHANGE_OUTPUT>'''

XML_RESP_USERLIST = b'''<?xml version="1.0" encoding="UTF-8" ?>
<!DOCTYPE USER_LIST_OUTPUT SYSTEM
"https://qualysapi.qg3.apps.qualys.com/user_list_output.dtd">
<USER_LIST_OUTPUT>
  <USER_LIST>
    <USER>
      <USER_LOGIN>test</USER_LOGIN>
      <USER_ID>1234</USER_ID>
      <EXTERNAL_ID></EXTERNAL_ID>
    </USER>
  </USER_LIST>
</USER_LIST_OUTPUT>'''

XML_RESP_EXPIRED = b'''<?xml version="1.0" encoding="UTF-8" ?>
<!DOCTYPE GENERIC_RETURN SYSTEM
"https://qualysguard.qg3.apps.qualys.com/generic_return.dtd">
<!-- This report was generated with an evaluation version of Qualys //-->
<GENERIC_RETURN>
  <API name="login" username="test" at="2021-05-06T23:15:07Z" />
  <RETURN status="FAILED" number="2001">
    Account Expired
  </RETURN>
</GENERIC_RETURN>'''


class TestQualysClient(unittest.TestCase):
    @patch.object(qualys.requests, 'request')
    def test__init(self,  mk_req):
        resp = Response()
        resp.status_code = 200
        resp._content = XML_RESP_USERLIST
        mk_req.return_value = resp

        qualys.QualysClient(
            platform=CREDS['platform'],
            username=CREDS['username'],
            password=CREDS['password']
        )

        mk_req.assert_called_once_with(
            'GET',
            'https://qualysapi.qg3.apps.qualys.com/msp/user_list.php',
            auth=('user', 'pass'),
            headers={
              'Accept': 'application/json',
              'Content-Type': 'application/json'
            },
            params=None
        )

    @patch.object(qualys.requests, 'request')
    def test__init_fail(self,  mk_req):
        resp = Response()
        resp.status_code = 200
        resp._content = XML_RESP_USERLIST
        mk_req.return_value = resp

        qualys.QualysClient._user_list = MagicMock()
        qualys.QualysClient._user_list.return_value = []

        with self.assertRaises(qualys.ConnectionException):
            qualys.QualysClient(
                platform=CREDS['platform'],
                username=CREDS['username'],
                password=CREDS['password']
            )

    @patch.object(qualys.requests, 'request')
    def test__change_pass(self, mk_req):
        resp = Response()
        resp.status_code = 200
        resp._content = XML_RESP_USERLIST
        mk_req.return_value = resp

        q_client = qualys.QualysClient(
            platform=CREDS['platform'],
            username=CREDS['username'],
            password=CREDS['password']
        )

        resp._content = XML_RESP_PWCHG
        mk_req.return_value = resp

        c_result = q_client.change_passwd('admin')

        self.assertEqual(c_result, 'Password123')

    @patch.object(qualys.requests, 'request')
    def test__change_pass_fail(self, mk_req):
        resp = Response()
        resp.status_code = 200
        resp._content = XML_RESP_USERLIST
        mk_req.return_value = resp

        q_client = qualys.QualysClient(
            platform=CREDS['platform'],
            username=CREDS['username'],
            password=CREDS['password']
        )

        resp._content = XML_RESP_EXPIRED
        mk_req.return_value = resp

        with self.assertRaises(qualys.ConnectionException):
            q_client.change_passwd('admin')
