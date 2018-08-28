import logging, json, traceback, asyncio
from tornado import web

def assign_objects(isetools_obj):
    global ise_obj
    ise_obj = isetools_obj

class Test(web.RequestHandler):
    async def get(self):
        try:
            ise_obj.test_ise_version()
            self.write({'result': "OK"})
        except:
            self.set_status(500)
            self.write({'error': "ISE Server unreachable or could not authenticate"})
        finally:
            self.finish()

class PSK(web.RequestHandler):
    async def get(self):
        mac = self.get_argument('mac', None)
        try:
            if not mac:
                raise ValueError("Missing argument 'mac'")

            response = ise_obj.get_endpointid(mac)
            self.write({'result': (response[0] if response else None)})
        except ValueError as e:
            self.set_status(400)
            self.write({'error': str(e)})
        except Exception as e:
            traceback.print_exc()
            self.set_status(500)
            self.write({'error': str(e)})
        finally:
            self.finish()

    async def post(self):
        # support both JSON bodies and URL arguments/parameters
        if self.request.headers.get('Content-Type') =='application/json':
            try:
                args = json.loads(self.request.body)
            except ValueError:
                traceback.print_exc()
                self.set_status(400)
                self.write({'error': "No JSON object found"})
                self.finish()
                return
        else:
            args = { k: self.get_argument(k, None)
                    for k in self.request.arguments }
        mac = args.get('mac', None)
        psk = args.get('psk', None)
        unid = args.get('unid', None)
        fname = args.get('firstname', None)
        lname = args.get('lastname', None)

        try:
            if not mac or not psk or not unid or not fname or not lname:
                raise ValueError("Missing argument: mac, psk, unid, fname, " +
                        "and lname are required.")
            mac = ise_obj.parse_mac(mac)
            logging.info(unid + " is attempting to create/update iPSK for "+mac)
            responseCode = ise_obj.set_psk(mac, psk, unid)
            logging.info("Response code " + responseCode + " received for " +
                    "iPSK change in ISE for " + mac)
            self.write({'result': 'iPSK succesfully updated/created.'})
        except ValueError as e:
            traceback.print_exc()
            self.set_status(400)
            self.write({'error': str(e)})
        except Exception as e:
            traceback.print_exc()
            self.set_status(500)
            self.write({'error': str(e)})
        finally:
            self.finish()

handlers = [
    (r"/ise/psk", PSK),
    (r"/ise/test", Test),
]
