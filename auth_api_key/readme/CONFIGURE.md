The api key menu is available into Settings \> Technical in debug mode.

By default, when you create an API key, only a hash of the key is
stored: the key can be read only when it is created, and a lost key must
be replaced by a new one. A database leak, a backup or a restored dump
does not expose usable keys.

This can be disabled in the general settings (debug mode, "Store API
keys hashed"), in which case the keys are stored as they are. Enabling
it later also hashes the keys already stored. On databases having keys
when the feature was introduced, it is left disabled by the upgrade.

If you want to manage them via serve environment settings use
auth_api_key_server_env, which never hashes the keys.
