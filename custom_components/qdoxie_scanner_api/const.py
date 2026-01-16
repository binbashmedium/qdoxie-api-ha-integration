"""Constants for qdoxie-scanner-api integration."""

DOMAIN = "qdoxie_scanner_api"

# Doxie
CONF_DOXIE_HOST = "doxie_host"
CONF_DOXIE_PORT = "doxie_port"
CONF_DOXIE_PASSWORD = "doxie_password"

DEFAULT_DOXIE_PORT = 80

# Modes
CONF_MODE = "mode"
MODE_PAPERLESS = "paperless"
MODE_CONSUME_DIR = "consume_dir"

# Paperless
CONF_PAPERLESS_URL = "paperless_url"
CONF_PAPERLESS_TOKEN = "paperless_token"
CONF_PAPERLESS_USERNAME = "paperless_username"
CONF_PAPERLESS_PASSWORD = "paperless_password"

# Consume
CONF_CONSUME_DIR = "consume_dir"

# Behaviour
CONF_INTERVAL_SECONDS = "interval_seconds"
CONF_DELETE_ON_SUCCESS = "delete_on_success"
CONF_WAIT_FOR_TASK = "wait_for_task"

DEFAULT_INTERVAL_SECONDS = 300
