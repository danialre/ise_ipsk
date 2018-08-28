import traceback, logging, signal, time, ssl
from functools import partial
from tornado import httpserver, ioloop, log
from tornado.web import Application

import settings, isetools, isehandlers, ruckushandlers

PORT = 2443

def create_server(serverlist, username, password, emailer=None, certfile=None,
        keyfile=None):
    """Create a Tornado server/app object.
    """
    isetools_obj = isetools.ISETools(serverlist, username, password, emailer)
    isehandlers.assign_objects(isetools_obj)
    handlers = isehandlers.handlers + ruckushandlers.handlers
    app = Application(handlers, debug=True)

    if certfile and keyfile:
        print(certfile)
        print(keyfile)
        # Enable HTTPS if certificates are available
        ssl_ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        ssl_ctx.load_cert_chain(certfile, keyfile)
        return httpserver.HTTPServer(app, ssl_options=ssl_ctx)
    else:
        # Otherwise set up for a front-end proxy (like nginx)
        return httpserver.HTTPServer(app, xheaders=True)

def signal_handler(server, sig, frame):
    """Handle shutdown signals (like SIGTERM) to shut off the web server
    gracefully.
    """
    io_loop = ioloop.IOLoop.current()
    def stop_loop(deadline):
        if (time.time() < deadline and
                (io_loop._callbacks or io_loop._timeouts)): #pylint: disable=no-member
            io_loop.add_timeout(time.time() + 1, stop_loop, deadline)
        else:
            io_loop.stop()

    def shutdown():
        logging.info('Signal received, stopping web server')
        server.stop()
        # wait 2 seconds after receiving SIGINT to complete requests
        stop_loop(time.time() + 2)

    io_loop.add_callback_from_signal(shutdown)

if __name__ == "__main__":
    if not hasattr(settings, 'ISE_SERVERLIST'):
        raise ValueError("settings.py missing ISE_SERVERLIST (list of IP/FQDN strings)")
    elif not hasattr(settings, 'ISE_USERNAME'):
        raise ValueError("settings.py missing ISE_USERNAME (string)")
    elif not hasattr(settings, 'ISE_PASSWORD'):
        raise ValueError("settings.py missing ISE_PASSWORD (string)")
    elif not hasattr(settings, 'CERTFILE'):
        raise ValueError("settings.py missing CERTFILE (HTTPS certificate .cer filename)")
    elif not hasattr(settings, 'KEYFILE'):
        raise ValueError("settings.py missing KEYFILE (HTTPS private key .key filesname)")

    log.enable_pretty_logging() # set up Tornado-formatted loggging
    logging.root.handlers[0].setFormatter(log.LogFormatter())
    server = create_server(settings.ISE_SERVERLIST, settings.ISE_USERNAME,
            settings.ISE_PASSWORD, certfile=settings.CERTFILE,
            keyfile=settings.KEYFILE)

    signal.signal(signal.SIGTERM, partial(signal_handler, server))
    signal.signal(signal.SIGINT, partial(signal_handler, server))

    logging.info("Starting...")
    server.listen(PORT)
    ioloop.IOLoop.current().start()
    logging.info("Stopping...")
