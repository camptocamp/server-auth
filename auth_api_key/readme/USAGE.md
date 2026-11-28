To apply this authentication system to your http request you must set
'api_key' as value for the 'auth' parameter of your route definition
into your controller.

``` python
class MyController(Controller):

    @route('/my_service', auth='api_key', ...)
    def my_service(self, *args, **kwargs):
        pass
```

The date of the last use of each key is recorded (at most once an hour),
which helps finding the keys that are not used anymore: the keys list
shows it and has filters for the keys never used or not used for 10, 30
or 60 days.
