# These handlers are used for Cloudpath - they implement the basics of a Ruckus
# Wireless Controller so DPSKs/IPSKs can be generated for Cloudpath.
#
import json, traceback, random, string, asyncio
from datetime import datetime
from tornado import web

zone_uuid = 'uuidzone1'
wlan_uuid = 'uuidwlan1'

class RuckusSession(web.RequestHandler):
    async def get(self):
        self.write({'apiVersions': "1_0", 'clientIp': self.request.remote_ip})
        self.finish()

    async def post(self):
        self.set_cookie('JSESSIONID', '123456') # make a special cookie
        self.write({'controllerVersion': "1"})
        self.finish()

class RuckusZones(web.RequestHandler):
    async def get(self):
        self.write({'totalCount': 1, 'hasMore': False, 'firstIndex': 0,
                'list': [{'id': zone_uuid, 'name': 'zone1'}] })
        self.finish()

class RuckusWLANs(web.RequestHandler):
    async def get(self):
        self.write({'totalCount': 1, 'hasMore': False, 'firstIndex': 0,
                'list': [{'id': wlan_uuid, 'zoneId': zone_uuid,
                'name': 'ULink', 'ssid': 'ULink'}] })
        self.finish()

class RuckusDPSK(web.RequestHandler):
    async def post(self):
        try:
            if self.request.files.keys():
                filename = list(self.request.files.keys())[0]
                fileinfo = self.request.files[filename][0]
            self.set_status(201)
            # password: all lowercase, 12 character randomly generated
            # also exclude vowels to avoid generating bad words
            passphrase = ''.join([random.choice('bcdfghjklmnpqrstvwxyz')
                    for _ in range(12)])
            self.write({'resultCount': 1, 'dpskInfoList': [ {
                    'id': "dpskid",
                    'wlanId': str(wlan_uuid),
                    'userName': str(fileinfo.get('body')).split(',')[0],
                    'macAddress': None,
                    # password: all lowercase, 16 character randomly generated
                    # also exclude vowels to avoid generating bad words
                    'passphrase': str(passphrase),
                    'vlanId': None,
                    "creationDateTime" : str(datetime.now().strftime(
                            '%Y/%m/%d %H:%M:%S')),
                    "expirationDateTime" : "Not start using"
                    }]})
        except:
            traceback.print_exc()
            self.set_status(500)
            self.write({})
        finally:
            self.finish()

class RegularDPSK(web.RequestHandler):
    async def get(self):
        try:
            # password: all lowercase, 12 character randomly generated
            # also exclude vowels to avoid generating bad words
            passphrase = ''.join([random.choice('bcdfghjklmnpqrstvwxyz')
                    for _ in range(12)])
            self.write({'result': str(passphrase)})
        except Exception as e:
            self.set_status(500)
            self.write({'error': str(e)})
        finally:
            self.finish()

handlers = [
    (r"/api/public/v4_0/session", RuckusSession),
    (r"/api/public/v4_0/rkszones", RuckusZones),
    ("/api/public/v4_0/rkszones/" + zone_uuid + "/wlans", RuckusWLANs),
    ("/api/public/v4_0/rkszones/" + zone_uuid + "/wlans/" + wlan_uuid +
            "/dpsk/upload", RuckusDPSK),
    ("/ise/psk/generate", RegularDPSK),
]
