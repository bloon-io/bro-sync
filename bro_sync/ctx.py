import ssl

class Ctx:
    CLOSE_SSL_CERT_VERIFY = True # for test only

    API_WSS_SSL_CONTEXT = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    API_WSS_SSL_CONTEXT.check_hostname = False  # for test only
    API_WSS_SSL_CONTEXT.verify_mode = ssl.CERT_NONE  # for test only

    SERVICE_SYNC_LOOP_INTERVAL = 2 # sec.

    DB_FILE_NAME = ".bro-sync.db"
    BLOON_DIRECT_LINK_URL_BASE = "https://localhost:8443/Bloon_Blink/share"
    
    BLOON_ADJ_API_WSS_URL = "wss://localhost:8443/Bloon_Adjutant/api"
    # BLOON_ADJ_API_WSS_URL = "wss://adj-xiaolongbao.bloon.io/Bloon_Adjutant/api"
    # BLOON_ADJ_API_WSS_URL = "wss://adj-stinky-tofu.bloon.io/Bloon_Adjutant/api"
    # BLOON_ADJ_API_WSS_URL = "wss://adj-bubble-tea.bloon.io/Bloon_Adjutant/api"