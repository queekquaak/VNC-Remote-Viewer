import os

# The port of api-server
API_SERVER_PORT = os.getenv("API_SERVER_PORT", "8080")

# Agent token for validations
API_AUTH_TOKEN = os.getenv("API_AUTH_TOKEN", "moneyprintergobrrr")

# The interval (in seconds) between metrics updates.
# Example: 300 seconds = 5 minutes
METRICS_UPDATE_INTERVAL = os.getenv("METRICS_UPDATE_INTERVAL", "60")

# The frequency of log rotation.
# Example: 'S', 'M', 'H', 'D', 'W0'-'W6', 'midnight'
LOG_WHEN = os.getenv("LOG_WHEN", "D")

# Interval between rotations in units specified in LOG_WHEN
# Example: LOG_WHEN: 'H' and LOG_INTERVAL: 2 - rotation every 2 hours
LOG_INTERVAL = os.getenv("LOG_INTERVAL", 1)

# The maximum number of stored log files
# If this number is exceeded, the oldest logs will be deleted
LOG_COUNT = os.getenv("LOG_COUNT", 30)
