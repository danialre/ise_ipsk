# These handlers are used for Cloudpath - they implement the basics of a Ruckus
# Wireless Controller so DPSKs/IPSKs can be generated for Cloudpath.
#
import json, traceback, random, string
from datetime import datetime
from common import common

zone_uuid = 'uuidzone1'
wlan_uuid = 'uuidwlan1'

class RuckusSession(common.BaseHandler):
    no_log = True
    @common.unblock
    def get(self):
        return {'apiVersions': "1_0", 'clientIp': self.request.remote_ip}

    @common.unblock
    def post(self):
        self.set_cookie('JSESSIONID', '123456') # make a special cookie
        return {'controllerVersion': "1"}

class RuckusZones(common.BaseHandler):
    no_log = True
    @common.unblock
    def get(self):
        return {'totalCount': 1, 'hasMore': False, 'firstIndex': 0,
                'list': [{'id': zone_uuid, 'name': 'zone1'}] }

class RuckusWLANs(common.BaseHandler):
    no_log = True
    @common.unblock
    def get(self):
        return {'totalCount': 1, 'hasMore': False, 'firstIndex': 0,
                'list': [{'id': wlan_uuid, 'zoneId': zone_uuid,
                'name': 'ULink', 'ssid': 'ULink'}] }

class RuckusDPSK(common.BaseHandler):
    @common.unblock
    def post(self):
        try:
            if self.request.files.keys():
                filename = self.request.files.keys()[0]
                fileinfo = self.request.files[filename][0]
            self.set_status(201)
            # password: all lowercase, 12 character randomly generated
            # also exclude vowels to avoid generating bad words
            passphrase = ''.join([random.choice('bcdfghjklmnpqrstvwxyz')
                    for _ in range(12)])
            return {'resultCount': 1, 'dpskInfoList': [ {
                    'id': "dpskid",
                    'wlanId': wlan_uuid,
                    'userName': fileinfo.get('body').split(',')[0],
                    'macAddress': None,
                    # password: all lowercase, 16 character randomly generated
                    # also exclude vowels to avoid generating bad words
                    'passphrase': passphrase,
                    'vlanId': None,
                    "creationDateTime" : datetime.now().strftime(
                            '%Y/%m/%d %H:%M:%S'),
                    "expirationDateTime" : "Not start using"
                    }]}
        except:
            traceback.print_exc()
            return {}

handlers = [
    (r"/api/public/v4_0/session", RuckusSession),
    (r"/api/public/v4_0/rkszones", RuckusZones),
    ("/api/public/v4_0/rkszones/" + zone_uuid + "/wlans", RuckusWLANs),
    ("/api/public/v4_0/rkszones/" + zone_uuid + "/wlans/" + wlan_uuid +
            "/dpsk/upload", RuckusDPSK)
]
