from zeep import Client
from zeep.cache import SqliteCache
from zeep.transports import Transport
from zeep.wsse.username import UsernameToken
from zeep import helpers
from requests import Session

class SalesforceMarketingCloudClient(object):
    def __init__(self, username, password, subdomain, mid, businessUnit):
        '''
        Initializes a Salesforce Marketing Cloud (via zeep) client

        :param username: The username (email) of the account
        :type username: :class:`string`
        :param password: Password used to connect
        :type password: :class:`passwd`
        :param subdomain: The subdomain to use. (From https://{SUB-DOMAIN}.soap.marketingcloudapis.com/ETFramework.wsdl)
        :type subdomain: :class:`string`
        :param mid: The target Account MID in the SFMC instance (multi-orgs only)
        :type mid: :class:`int`
        :param businessUnit: The target Business Unit MID in the SFMC instance (multi-orgs only)
        :type businessUnit: :class:`int`
        '''
        self._mid=mid
        self._businessUnit=businessUnit
        self._headers = {'SOAPAction': 'Update','Content-Type': 'text/xml'}
        wsdl="https://{}.soap.marketingcloudapis.com/ETFramework.wsdl".format(subdomain)

        # Set headers & Cache wsdl
        session = Session()
        session.headers.update({'SOAPAction': 'Update','Content-Type': 'text/xml'})
        transport = Transport(cache=SqliteCache(), session=session)

        # Init Zeep Client to SFMC
        self._client = Client(
            wsdl,
            transport=transport, 
            wsse=UsernameToken(username, password)
        )

    def get_sfmc_status(self):
        '''
        Grabs the current state of the Salesforce Marketing Cloud SOAP API

        :returns: Marketing Cloud API Status (OK / InMaintenance / UnplannedOutage)
        :rtype: :class:`string`
        '''

        response = self._client.service.GetSystemStatus()
        parsedResponse = helpers.serialize_object(response)

        return (parsedResponse['OverallStatus'])

    def change_passwd(self, username, newpassword):
        '''
        Changes a Salesforce Marketing Cloud User account password.

        :param username: The username (email) of the account
        :type username: :class:`string`
        :param newpassword: The new password to change to
        :type newpassword: :class:`string`

        :returns: True if successful
        :rtype: :class:`bool`
        '''

        # Retrieve Complex Types to build payload
        account_user_obj = self._client.get_type('ns0:AccountUser')
        sfmc_client_obj = self._client.get_type('ns0:ClientID')
        options_obj = self._client.get_type('ns0:UpdateOptions')
        
        # Construct User to update and Operation options
        user_options = options_obj()
        user = account_user_obj(
            UserID=username,
            Name=username,
            Email=username,
            Password=newpassword,
            BusinessUnit=self._businessUnit,
            Client=sfmc_client_obj(ID=self._mid)
        )

        # Check Sever is OK before posting a User Update
        serverStatus = self.get_sfmc_status()
        if (serverStatus != 'OK'):
            raise Exception(
                'Server Error: {}'.format(serverStatus)
            )

        # Send SOAP Update request
        response = self._client.service.Update(Options=user_options, Objects=user)
        parsedResponse = helpers.serialize_object(response)['Results'][0]

        # SFMC Soap response always responds StatusCode=200 unless server error. Actual error is in response 'results' body
        if (parsedResponse['StatusCode'] != 'OK'):
            raise Exception(
                'Failed to change password. Error: {} {}'.format(parsedResponse['ErrorCode'], parsedResponse['StatusMessage'])
            )
        
        return True
