To apply this authentication system to your http request you must set
'api_key' as value for the 'auth' parameter of your route definition
into your controller.

``` python
class MyController(Controller):

    @route('/my_service', auth='api_key', ...)
    def my_service(self, *args, **kwargs):
        pass
```

An API key can have an expiration date: it is refused after it. To rotate
a key without interruption, create the new key, switch the callers to it,
then set an expiration date on the old one (or archive it).

The date of the last use of each key is recorded (at most once an hour),
which helps finding the keys that are not used anymore: see the "Never
used" filter of the keys list.
