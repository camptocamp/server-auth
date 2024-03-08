# How to test IMAP

## Start mailcatcher and set up

In the development environment, a [MailCatcher](https://github.com/estelora/docker-mailcatcher-imap) container can be started alongside Odoo.

    docker-compose up mailcatcher
    
The RoundCube service is published by default  on `localhost:1080` and with `mailcatcher`as default username and password.

In Odoo add a new Incoming Mail Server 

    Server Type: IMAP server
    Server Name: mailcather
    Port: 143
    Username: mailcatcher
    Password: mailcatcher

And click the `Test & Confirm` button.

## How to reproduce a production issue

To reproduce a real case we need to send an email to the RoundCube mail client.
First we need the real email that we want to troubleshoot. In Gmail this can be done by clicking `Download Message` from the top right menu `...`  on an open message. The file format will be `.eml`

Then using the `sendemail` command line tool:

    apt install sendemail

We can upload the previously downloaded file (IMO the from address has no impact but is required):

    sendemail -s localhost:1025  -o message-file={/path/to/the/email_file.elm} -o message-format=raw -f {from address}

Now we should see our new email in the RoundCube interface that can be processed by our Odoo dev instance by clicking `Fetch Now` from our previously configured IMAP server.

## More ressources

There is also a [SATK presentation](https://confluence.camptocamp.com/confluence/display/BS/2023-03-02+SatK+-+test+incoming+mails+-+logging+-+deprecation+warnings+in+base_rest+-+fast_api%2C+future+of+base_rest) related to this.
