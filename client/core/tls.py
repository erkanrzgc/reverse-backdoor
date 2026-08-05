import ssl


def create_ssl_context(certfile=None, keyfile=None, server_side=False, verify=True):
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER if server_side else ssl.PROTOCOL_TLS_CLIENT)
    ctx.check_hostname = verify
    ctx.verify_mode = ssl.CERT_REQUIRED if verify else ssl.CERT_NONE

    ctx.minimum_version = ssl.TLSVersion.TLSv1_2
    ctx.set_ciphers(
        'ECDHE-ECDSA-AES256-GCM-SHA384:'
        'ECDHE-RSA-AES256-GCM-SHA384:'
        'ECDHE-ECDSA-AES128-GCM-SHA256:'
        'ECDHE-RSA-AES128-GCM-SHA256'
    )

    if certfile and keyfile:
        ctx.load_cert_chain(certfile, keyfile)
    elif server_side:
        ctx.load_default_certs()

    ctx.set_ecdh_curve('prime256v1')
    ctx.options |= ssl.OP_NO_COMPRESSION

    return ctx


def wrap_client_socket(sock, hostname=None):
    ctx = create_ssl_context(server_side=False, verify=False)
    try:
        return ctx.wrap_socket(sock, server_hostname=hostname)
    except Exception:
        raise ConnectionError("TLS handshake failed")


def wrap_server_socket(sock, certfile=None, keyfile=None):
    ctx = create_ssl_context(certfile=certfile, keyfile=keyfile, server_side=True, verify=False)
    try:
        return ctx.wrap_socket(sock, server_side=True)
    except Exception:
        raise ConnectionError("TLS server handshake failed")
