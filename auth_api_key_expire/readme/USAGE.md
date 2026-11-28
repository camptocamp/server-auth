Set the expiration date on an API key (leave it empty for a key that
does not expire). The key is refused after this date, without any other
action.

Each user of the configured group gets one To Do, on their own contact,
listing all the keys about to expire, with a link to the keys. Marking it
done does not create it again; changing the expiration date of a key
does, when the new date comes close.

To rotate a key without interruption, create the new key, switch the
callers to it, then set an expiration date on the old one (or archive
it).
