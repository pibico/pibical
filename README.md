## PibiCal

Frappe App for Events syncronization with CalDav and iCalendar

## License

MIT

## Requirements
Requires a Frappe server instance (refer to https://github.com/frappe/frappe), and has dependencies on CalDav (refer to https://github.com/python-caldav/caldav) and icalendar (refer to https://github.com/collective/icalendar).

## Compatibility
PibiCal has been tested on Frappe/ERPNext version-12 and version-13 as well join together with NextCloud on server with TLS active and NOT with wildcard certificate.

## Installation
From the frappe-bench folder, execute (change branch to the proper version of Frappe/ERPNext)
```
$ bench get-app pibical https://github.com/pibico/pibical.git --branch version-12
$ bench install-app pibical
```
If you are using a multi-tenant environment, use the following command
```
$ bench --site site_name install-app pibical
```

## Update
Run updates with
```
$ bench update
```
In case you update from the sources and observe errors, make sure to update dependencies with
```
$ bench update --requirements
```

## Features
Once installed, you will have in your User some new custom fields for giving the credentials of the NextCloud CalDav Server.

![imagen](https://user-images.githubusercontent.com/69711454/139237194-4edf0621-4002-4bd2-bbf1-1e1b91c17b23.png)

You must provide your NextCloud CalDav Server url (Caldav URL) as  https://domain.com/remote.php/dav/principals/
then you will bring your NextCloud User as username@domain.com or whichever name you will have in NextCloud
at last you will inform about yor NextCloud User Password or Token if you have created one.

With these credentials you will be able to syncronize your Frappe/ERPNext Public events (only Public Events) with your NextCloud Server CalDav Calendars.

If you create now a Calendar Event in Frappe/ERPNext, provided you have selected public in event_type and you have activated Sync with CalDav, the NextCloud CalDav calendars your user has wil be shown on the dropdown Caldav ID Calendar as in the picture.

![imagen](https://user-images.githubusercontent.com/69711454/139238862-d947d264-49a3-4812-b86c-38f7f5f811e9.png)

You can provide more details to your event, such as repetition, participants, and even create minutes of meetings on the event.

![imagen](https://user-images.githubusercontent.com/69711454/139239301-349e96b9-cfd9-4993-a786-a9209f43c4ae.png)

After saving the event, after some seconds depending on your connection to the NextCloud Calendar Server since you have a syncronous call, on Frappe/ERPNext you will see a new created event on your NextCloud CalDav Server.

![imagen](https://user-images.githubusercontent.com/69711454/139239487-4a751e7a-19d4-4e9d-bd2a-5d1309e2d514.png)

You will be able to see the event created on NextCloud also.

![imagen](https://user-images.githubusercontent.com/69711454/139239937-8ba55a3a-f24d-4fe6-ad94-2cd5c49c2e02.png)

Syncronization from NextCloud CalDav Server is done every 3 minutes. You can change this settings in hooks.py on the app.

## Future Development
Future improvements can be related to Sending Invitations to Selected Participants in Child Table with event.ics attachment to Participants, etc.
