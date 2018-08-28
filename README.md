ISE ISPK REST Handlers
======================

This project provides a simple REST API to use for registering Individual PSKs
(IPSKs) with Cisco ISE. This is specifically designed with Ruckus Cloudpath in mind,
using the DPSK Ruckus Controller and REST API Call Workflow steps to generate and
set up an IPSK.

Project/Container setup
-----------------------
1. First step is to create `settings.py` within the project folder and fill it out
with org-specific information.
```
EMAIL_FROM='no-reply@example.com'
IPSK_ADMINS = ['adminuser@example.com', 'adminintern@example.com']
ISE_SERVERLIST = ['ise1.example.com', 'ise2.example.com']
ISE_USERNAME = "ers_ipsk" # Note that this is an ERS user, NOT an ISE admin!
ISE_PASSWORD = "changeme"
GROUP_ID='' # Group alphanumeric ID from ISE
CERTFILE = 'webserver.cer' # Leave this as webserver.cer to autogenerate a self-signed cert
KEYFILE = 'webserver.key'  # Leave this as webserver.cer to autogenerate a self-signed key
```

- (Optional) copy an HTTPS certificate and private key to the project, and match
the filenames with what is in `settings.py`.

- Build the Docker image within the project folder.
```
docker build -t isepsk .
```

- Run the Docker image, making the container listen to port 443 (REST API calls)
and 7443 (optional, required for Ruckus Controller emulation if the "Generate a Ruckus DPSK"
workflow step is used in Cloudpath)
```
docker run -p 7443:2443 -p 443:2443 isepsk
```

API Reference
-------------
- `GET https://<container url>/ise/test` Check ISE server reachability without inserting PSKs.
This call is useful for health checks.
    - Arguments: None
    - Returns:
    ```
    # successful call
    {"result": "OK"}

    # unsuccessful call, failure between the container and the ISE Server(s)
    {"error": "ISE Server unreachable or could not authenticate"}
    ```
- `GET https://<container url>/ise/psk` Get the status of a device's MAC address in ISE.
    - Arguments: Acceptable as URL arguments.
        - mac: MAC address as a string, with any delimiter type and/or style
    - Returns:
    ```
    # successful call
    {"result": "74317d60-9c9b-1118-ab3e-0050596dbc91"} # or similar ISE object ID

    # successful call, no device found
    {"result": null}

    # unsuccessful call, will also return a 500 status code
    {"error": <other error message as a string>}
    ```
- `POST https://<container url>/ise/psk` Add an IPSK to ISE. This is the main call that
sends to ISE.
    - Arguments: Acceptable as a JSON body or as URL arguments
        - mac: MAC address as a string, with any delimiter type and/or style
        - psk: PSK as a string
        - unid: User ID as a string
        - firstname: First name of the User
        - lastname: Last name of the User
    - Returns:
    ```
    # successful call, will also return a 201 status code
    {"result": "iPSK succesfully updated/created."}

    # unsuccessful call, missing parameters, will also return a 400 status code
    {"error": "Missing argument: mac, psk, unid, fname, and lname are required." }

    # unsuccessful call, will also return a 500 status code
    {"error": <other error message as a string>}
    ```
- `GET https://<container url>/ise/psk/generate` Generate a 16-character PSK.
    - Arguments: None
    - Returns:
    ```
    # successful call
    {"result": <PSK as a string>}
    ```

Authors
-------
Written by Brian Sorensen (brian.sorensen@utah.edu) and Danial Ebling (danial.ebling@utah.edu) for the University of Utah.
