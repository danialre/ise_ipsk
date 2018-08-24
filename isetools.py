import requests, logging, json
import xml.etree.ElementTree as ElemTree
from bs4 import BeautifulSoup

import settings

class ISEAPIError(Exception):
    """
    An error with the ISE API call being made.
    """
    pass

class ISETools(object):
    """Collection of utilities to interface with Cisco ISE.

    Args:
        url: Server URL as a string.
        username: ISE service account username as a string.
        password: ISE service account password as a string.
    """
    get_headers = {'Accept':
            'application/vnd.com.cisco.ise.identity.endpoint.1.0+xml'}
    put_headers = {'Content-Type':
            'application/vnd.com.cisco.ise.identity.endpoint.1.0+xml'}
    post_headers = {'Content-Type':
            'application/vnd.com.cisco.ise.identity.endpoint.1.0+xml'}
    delete_headers = {'Accept':
            'application/vnd.com.cisco.ise.identity.endpoint.1.0+xml'}

    def __init__(self, serverlist, username, password, emailer):
        self.serverlist = serverlist
        self.serverindex = 0
        self.auth = (username, password)
        self.emailer = emailer

    def url(self):
        """This autogenerates and returns the URL and server to use.

        Returns:
            URL prefix as a string.
        """
        return ('https://' + self.serverlist[self.serverindex] +
                ':9060/ers/config/')

    def next_server(self):
        """Switch to the next known server. This does not accept or return
        anything.
        """
        self.serverindex += 1
        if self.serverindex >= len(self.serverlist):
            self.serverindex = 0

    def get_dev_info(self):
    #Current development status
        return "Production"

    def parse_mac(self, mac):
        """Takes in a mac address and converts it to colon-separated formatting.
        Throws a SyntaxError if the mac is not 12 characters without formatting.

        Args:
            mac: The MAC address to format.

        Returns:
            mac formatted Cisco style.
        """
        mac = mac.upper()
        # Strips everything but the hexadecimal characters.
        mac = ''.join(char for char in mac if char in 'ABCDEF0123456789')
        if len(mac) != 12:
            raise SyntaxError('MAC Address needs to be 12 characters')
        # Places colons between every 2 characters.
        return ':'.join(mac[i:i+2] for i in range(0, len(mac), 2))

    def test_ise_version(self, retries=0):
        """Test ISE connectivity and service account validity. Note that this
        does not check to see if the current server is the active one (if set up
        for HA).

        Args:
            retries: Optional retry attempt number as an integer.

        Returns:
            True for successful, False otherwise.
        """
        if retries >= 3: # retried too many times, give up
            return False

        url = self.url() + "service/versioninfo"
        try:
            result = requests.get(url,
                    headers={'Content-Type': 'application/json',
                    'Accept': 'application/json'}, auth=self.auth, timeout=5)
            json.loads(result.text)
            return True
        except requests.exceptions.Timeout:
            # switch to next ISE server and try again
            logging.warn(self.serverlist[self.serverindex] +
                    ' timed out, cycling...')
            self.next_server()
            return self.test_ise_version(retries=(retries + 1))
        except:
            return False

    def get_endpointid(self, mac):
        """Get the EndpointID for an endpoint MAC address.

        Args:
            mac: MAC address as a string.

        Returns:
            endpointID: Endpoint ID as a string if endpoint exists, or None
            type if none exists.
            responseCode: HTTP status code result of endpointID inquiry.
        """
        url = self.url() + "endpoint?filter=mac.EQ." + mac

        result = requests.get(url, headers=self.get_headers, auth=self.auth)
        try:
            root = ElemTree.fromstring(result.text)
            responseCode = str(result).split('[')[1].split(']')[0]

            for child in root.iter():
                if 'id' in child.attrib:
                    endpointid = child.attrib['id']
                    return endpointid, responseCode
        except:
            soup = BeautifulSoup(result.text, 'html.parser')
            #get summary of html response
            errorsummary = soup.body.h1.get_text()
            #get details of html response
            errordescription = (soup.body.find('p').findNext('p').get_text(
                    ).split('Description ')[1])
            #bundle error details for logging
            logging.error(errorsummary + ": " + errordescription)
            #raise details as exception
            raise ISEAPIError(errordescription)

    def put_psk(self, mac, psk, unid):
        """Update an endpoint entry with MAC address, uNID, and PSK.

        Args:
            mac: MAC address as a string.
            psk: PSK as a string.
            unid: uNID as a string.

        Returns:
            responseCode: HTTP status code result of attempted change.
        """
        url = self.url() + "endpoint/" + self.get_endpointid(mac)[0]

        xml = """<?xml version='1.0' encoding='UTF-8' standalone='yes'?>
                <ns3:endpoint name='name' id='id' description='description'
                xmlns:ns2='ers.ise.cisco.com'
                xmlns:ns3='identity.ers.ise.cisco.com'>
                    <customAttributes>
                        <customAttributes>
                            <entry>
                                <key>iPSK</key>
                                <value>psk=""" + psk + """</value>
                            </entry>
                        </customAttributes>
                    </customAttributes>
                <groupId>""" + settings.GROUP_ID + """</groupId>
                <identityStore></identityStore>
                <identityStoreId></identityStoreId>
                <mac>""" + mac + """</mac>
                <portalUser>""" + unid + """</portalUser>
                <profileId></profileId>
                <ipsk>""" + psk + """</ipsk>
                <staticGroupAssignment>true</staticGroupAssignment>
                <staticProfileAssignment>false</staticProfileAssignment>
                </ns3:endpoint>"""

        result = (requests.put(url, headers=self.put_headers, data=xml,
                auth=self.auth))
        responseCode = str(result).split('[')[1].split(']')[0]

        return responseCode

    def create_psk(self, mac, psk, unid, retries=0):
        """Create a new endpoint to add a PSK for a MAC address and uNID.

        Args:
            mac: MAC address as a string.
            psk: PSK as a string.
            unid: uNID as a string.
            retries: Optional retry attempt number as an integer.

        Returns:
            responseCode: HTTP status code result of attempted change.
        """
        if retries >= 3: # retried too many times, give up
            raise ISEAPIError('No ISE servers could be reached')
        url = self.url() + "endpoint/"

        xml = """<?xml version='1.0' encoding='UTF-8' standalone='yes'?>
                <ns3:endpoint name='name' id='id' description='description'
                xmlns:ns2='ers.ise.cisco.com'
                xmlns:ns3='identity.ers.ise.cisco.com'>
                    <customAttributes>
                        <customAttributes>
                            <entry>
                                <key>iPSK</key>
                                <value>psk=""" + psk + """</value>
                            </entry>
                        </customAttributes>
                    </customAttributes>
                <groupId>""" + settings.GROUP_ID + """</groupId>
                <identityStore></identityStore>
                <identityStoreId></identityStoreId>
                <mac>""" + mac + """</mac>
                <portalUser>""" + unid + """</portalUser>
                <profileId></profileId>
                <staticGroupAssignment>true</staticGroupAssignment>
                <staticProfileAssignment>false</staticProfileAssignment>
                </ns3:endpoint>"""

        try:
            result = (requests.post(url, headers=self.post_headers, data=xml,
                    auth=self.auth, timeout=10))
            if (result.status_code == 401 and
                    'operation is allowed on pap node only'
                    in result.text.lower()):
                # switch to next ISE server and try again
                logging.warn(self.serverlist[self.serverindex] +
                        ' is not primary node, cycling...')
                self.next_server()
                return self.create_psk(mac, psk, unid, retries=(retries + 1))
            else:
                return str(result.status_code)
        except requests.exceptions.Timeout:
            # switch to next ISE server and try again
            logging.warn(self.serverlist[self.serverindex] +
                    ' timed out, cycling...')
            self.next_server()
            return self.create_psk(mac, psk, unid, retries=(retries + 1))

    def delete_endpoint(self, mac, unid, retries=0):
        """Delete an enpoint. This is useful for when an iPSK needs to be
        updated.

        Args:
            mac: MAC address as a string.
            unid: uNID as a string.
            retries: Optional retry attempt number as an integer.

        Returns:
            Response code as a string.
        """
        if retries >= 3: # retried too many times, give up
            raise ISEAPIError('No ISE servers could be reached')
        url = self.url() + "endpoint/" + self.get_endpointid(mac)[0]

        try:
            result = (requests.delete(url, headers=self.delete_headers,
                    auth=self.auth, timeout=10))
            if (result.status_code == 401 and
                    'operation is allowed on pap node only'
                    in result.text.lower()):
                # switch to next ISE server and try again
                logging.warn(self.serverlist[self.serverindex] +
                        ' is not primary node, cycling...')
                self.next_server()
                return self.delete_endpoint(mac, unid, retries=(retries + 1))
            else:
                return str(result.status_code)
        except requests.exceptions.Timeout:
            # switch to next ISE server and try again
            logging.warn(self.serverlist[self.serverindex] +
                    ' timed out, cycling...')
            self.next_server()
            return self.delete_endpoint(mac, unid, retries=(retries + 1))

    def set_psk(self, mac, psk, unid):
        """Set a PSK for an endpoint, choose to edit existing endpoint or
        create new one based off of return from get_endpointid().

        Args:
            mac: MAC address as a string.
            psk: PSK as a string.
            unid: uNID as a string.

        Returns:
            XML details of endpoint.
        """
        endpointid = self.get_endpointid(mac)

        if not endpointid:
            return self.create_psk(mac, psk, unid)
        else:
            self.delete_endpoint(mac, unid)
            return self.create_psk(mac, psk, unid)

    def send_email(self, responseCode, unid, fname, lname, mac):
        """Send an email for unsuccessful registrations.

        Args:
            responseCode: Response code from ISE as a string.
            unid: uNID of the affected user as a string.
            fname: First name of the user as a string.
            lname: Last name of the user as a string.
            mac: Attempted MAC address as a string.
        """
        if responseCode.startswith('2'):
            return # Cloudpath already sends an email for successful
                   # registrations

        EMAIL_TO = unid + '@utah.edu'
        # email header details
        message = ('Dear ' + fname + ' ' + lname + ', <br><p>' +
                'Thank you for using onboard.utah.edu to register your IoT ' +
                'device to connect with the University of Utah ULink network. '+
                ' Unfortunately, we were unable to successfully register your '+
                'device.<br><br>Please try again. Note: Devices on ULink must '+
                'register the hardware, or MAC, address (view instructions at '+
                '<a href="http://bit.ly/finding-mac-for-ulink">' +
                'http://bit.ly/finding-mac-for-ulink</a>). Then use your MAC ' +
                'address to register your device via ' +
                '<a href="https://onboard.utah.edu/">' +
                'https://onboard.utah.edu/</a>.<br><br>' +
                'Your device with MAC address ' + mac + ', and associated '+
                'password or pre-shared key (PSK), should be configured as ' +
                'follows in order to connect:<br><br>' +
                'SSID: ULink<br>Authentication: WPA2-Personal<br>Encryption: ' +
                'AES<br><br>Please note: The ULink network is not intended ' +
                'for laptops, smartphones, or tablets that are capable of '+
                'connecting to UConnect.<br><br>For more information about ' +
                "ULink, copy/paste the following link into your browser's " +
                "address bar: " +
                '<a href="http://bit.ly/ulink-device-configuration">' +
                'http://bit.ly/ulink-device-configuration</a>.<br><br>' +
                "If you're still unsuccessful after trying to register " +
                'your device again, please contact the UIT Help Desk ' +
                '(801-581-4000, option 1) for technical assistance.</p>')
        message_footer = ('Best regards,<br><br>University ' +
                'Information Technology<br>The University of Utah<br>' +
                '102 S 200 E Ste. 110<br>Salt Lake City, UT 84111<br>UIT Help '+
                'Desk: 801-581-4000 x 1')

        self.emailer.send_email(('ULink device registration status for ' + mac),
                message, EMAIL_TO, html=True, footer=message_footer,
                sender=settings.EMAIL_FROM)

        # also send an email to IPSK admins
        admin_message = ("<p>A recent IOT device registration failed on ULink."+
                "<br><br>MAC Address: " + str(mac) +
                "<br>uNID: " + str(unid) +
                "<br>Response code from ISE: " + str(responseCode) + "</p><p>" +
                "Please view TOAST logs for more information, or use this " +
                "API call to test TOAST's connectivity/service account to ISE:"+
                "<br>(GET) https://toast.utah.edu/ise/test</p>")
        self.emailer.send_email('ULink device registration failure',
                admin_message, settings.IPSK_ADMINS, html=True)
