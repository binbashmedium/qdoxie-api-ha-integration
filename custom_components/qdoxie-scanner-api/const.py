"""Constants for Doxie -> Paperless-ngx integration."""

DOMAIN = "doxie_paperless"

CONF_DOXIE_HOST = "doxie_host"
CONF_DOXIE_PORT = "doxie_port"
CONF_DOXIE_PASSWORD = "doxie_password"

CONF_PAPERLESS_URL = "paperless_url"
CONF_PAPERLESS_TOKEN = "paperless_token"
CONF_PAPERLESS_USERNAME = "paperless_username"
CONF_PAPERLESS_PASSWORD = "paperless_password"

CONF_INTERVAL_SECONDS = "interval_seconds"
CONF_MODE = "mode"
CONF_CONSUME_DIR = "consume_dir"
CONF_DELETE_ON_SUCCESS = "delete_on_success"
CONF_WAIT_FOR_TASK = "wait_for_task"

MODE_PAPERLESS = "paperless"
MODE_CONSUME_DIR = "consume_dir"

DEFAULT_DOXIE_PORT = 80
DEFAULT_INTERVAL_SECONDS = 60

PLATFORMS = ["sensor"]

SERVICE_SYNC_NOW = "sync_now"
