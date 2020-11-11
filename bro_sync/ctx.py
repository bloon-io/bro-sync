import ssl

class Ctx:
    CLOSE_SSL_CERT_VERIFY = False

    API_WSS_SSL_CONTEXT = True
    # API_WSS_SSL_CONTEXT = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    # API_WSS_SSL_CONTEXT.check_hostname = False  # for test only
    # API_WSS_SSL_CONTEXT.verify_mode = ssl.CERT_NONE  # for test only

    SYNC_DELAY_MODE_DELAY_SEC = 2

    DB_FILE_NAME = ".bro-sync.db"
    BLOON_DIRECT_LINK_URL_BASE = "https://direct.bloon.io/share"
    
    BLOON_ADJ_API_WSS_URL = "wss://adj.bloon.io/Bloon_Adjutant/api"
