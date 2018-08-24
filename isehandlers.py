import logging, json, traceback
from common import common

def assign_objects(isetools_obj):
    global ise_obj
    ise_obj = isetools_obj

class Test(common.BaseHandler):
    @common.unblock
    def get(self):
        try:
            ise_obj.test_ise_version()
            return {'result': "OK"}
        except:
            return {'error': "ISE Server unreachable or could not authenticate"}

class PSK(common.BaseHandler):
    @common.authenticated
    def get(self):
        mac = self.get_argument('mac', None)
        if not mac:
            return {'error': "Missing argument mac"}
        try:
            epid, responsecode = ise_obj.get_endpointid(mac)
            return {'result': epid}
        except Exception as e:
            return {'error': str(e)}

    @common.unblock # authentication isn't supported in the caller (Cloudpath)
    def post(self):
        if self.request.headers.get('Content-Type') =='application/json':
            try:
                args = json.loads(self.request.body)
            except ValueError:
                return {'error': "No JSON object found"}
        else:
            args = { k: self.get_argument(k, None)
                    for k in self.request.arguments }
        mac = args.get('mac', None)
        psk = args.get('psk', None)
        unid = args.get('unid', None)
        fname = args.get('firstname', None)
        lname = args.get('lastname', None)

        if (not mac) or (not psk) or (not unid) or (not fname) or (not lname):
            return {'error': "Missing argument: mac, psk, unid, fname, and " +
                    "lname are required."}

        try:
            mac = ise_obj.parse_mac(mac)
            logging.info(unid + " is attempting to create/update iPSK for "+mac)
            responseCode = ise_obj.set_psk(mac, psk, unid)
            logging.info("Response code " + responseCode + " received for " +
                    "iPSK change in ISE for " + mac)
            ise_obj.send_email(responseCode, unid, fname, lname, mac)
            return {'result': 'iPSK succesfully updated/created.'}
        except Exception as e:
            traceback.print_exc()
            ise_obj.send_email('500', unid, fname, lname, mac)
            return {'error': str(e)}

handlers = [
    (r"/ise/psk", PSK),
    (r"/ise/test", Test),
]
