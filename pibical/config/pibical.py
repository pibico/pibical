from __future__ import unicode_literals
from frappe import _

def get_data():
  return [
    {
      "label": _("PibiCal"),
      "icon": "fa fa-calendar",
      "items": [
        {
          "type": "doctype",
          "name": "Event",
          "description": _("Event"),
          "onboard": 1,
        },
        {
          "type": "doctype",
          "name": "User",
          "description": _("User"),
          "onboard": 1,
        },
        {
          "type": "doctype",
          "name": "SMS Settings",
          "description": _("SMS Settings"),
          "onboard": 1,
        }
      ]
    }
  ]
