from os import path
from socket import gethostname
from OpenSSL import crypto
from datetime import datetime

import settings

DEFAULT_CERT = 'webserver.cer'
DEFAULT_KEY  = 'webserver.key'

def setup_certs(certfile=None, keyfile=None):
    """Set up frontend HTTPS certificates and keys.

    Args:
        certfile: Optional non-default filename for the certificate.
        keyfile: Optional non-default filename for the private key.
        generate: If True, generate self-signed certificates with the default
            filenames.
        skip: If True, skip certificate setup altogether.

    Returns: Certificate filename and Key filename used or generated.
    """
    if not certfile or not keyfile:
        certfile = DEFAULT_CERT
        keyfile = DEFAULT_KEY

    # skip if cert and key already exist
    if path.isfile(certfile) and path.isfile(keyfile):
        print('skipping, ' + certfile + ' and ' + keyfile + ' already exist')
        return certfile, keyfile

    # create key pair
    print('generating ' + certfile + ' and ' + keyfile)
    k = crypto.PKey()
    k.generate_key(crypto.TYPE_RSA, 2048)

    # create a self-signed cert
    cert = crypto.X509()
    cert.get_subject().C = "US"
    cert.get_subject().ST = "Utah"
    cert.get_subject().L = "Salt Lake City"
    cert.get_subject().O = "UU"
    cert.get_subject().OU = "ISE PSK Selfsigned cert org"
    cert.get_subject().CN = gethostname()
    cert.set_serial_number(int(datetime.now().strftime('%Y%m%d%H%M%S')))
    cert.gmtime_adj_notBefore(0)
    cert.gmtime_adj_notAfter(1*365*24*60*60) # valid for one year
    cert.set_issuer(cert.get_subject())
    cert.set_pubkey(k)
    cert.sign(k, 'sha1')

    open(certfile, "wt").write(
            crypto.dump_certificate(crypto.FILETYPE_PEM, cert).decode())
    open(keyfile, "wt").write(
            crypto.dump_privatekey(crypto.FILETYPE_PEM, k).decode())
    return certfile, keyfile

if __name__ == '__main__':
    if not hasattr(settings, 'CERTFILE'):
        raise ValueError("settings.py missing CERTFILE (HTTPS certificate .cer filename)")
    elif not hasattr(settings, 'KEYFILE'):
        raise ValueError("settings.py missing KEYFILE (HTTPS private key .key filesname)")
    certfile, keyfile = setup_certs(certfile=settings.CERTFILE,
            keyfile=settings.KEYFILE)
