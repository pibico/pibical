# -*- coding: utf-8 -*-
# Copyright (c) 2020, PibiCo and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import msgprint, _
import datetime, json

import sys, requests, hashlib
from icalendar import Calendar, Event
from icalendar import vCalAddress, vText, vRecur
from pytz import UTC, timezone
from dateutil.rrule import *

import caldav
from frappe.utils.password import get_decrypted_password
madrid = timezone('Europe/Madrid')

@frappe.whitelist()
def get_calendar(nuser):
  fp_user = frappe.get_doc("User", nuser)
  if fp_user.caldav_url and fp_user.caldav_username and fp_user.caldav_token:
    if fp_user.caldav_url[-1] == "/":
      caldav_url = fp_user.caldav_url + "users/" + fp_user.caldav_username
    else:
      caldav_url = fp_user.caldav_url + "/users/" + fp_user.caldav_username
    # print(caldav_url)
    caldav_username = fp_user.caldav_username
    caldav_token = get_decrypted_password('User', nuser, 'caldav_token', False)
    # set connection to caldav calendar with user credentials
    caldav_client = caldav.DAVClient(url=caldav_url, username=caldav_username, password=caldav_token)
    cal_principal = caldav_client.principal()
    # fetching calendars from server
    calendars = cal_principal.calendars()
    arr_cal = []
    if calendars:
      # print("[INFO] Received %i calendars:" % len(calendars))
      cal_url = caldav_url.replace("principals/users","calendars")
      for c in calendars:
        print("Name: %-20s  URL: %s" % (c.name, c.url.replace(cal_url +"/" , "").replace("/","")))
        scal = {}
        scal['name'] = c.name
        scal['url'] = str(c.url)
        arr_cal.append(scal)
    else:
      frappe.msgprint(_("Server has no calendars for your user"))
    return arr_cal

@frappe.whitelist()
def sync_caldav_event_by_user(doc, method=None):
  if doc.sync_with_caldav:
    # Get CalDav Data from logged in user
    fp_user = frappe.get_doc("User", frappe.session.user)
    # Continue if CalDav Data exists on logged in user
    if fp_user.caldav_url and fp_user.caldav_username and fp_user.caldav_token:
      # Check if selected calendar matches with previously recorded and delete event if not matching
      if doc.caldav_id_url:
        s_cal = doc.caldav_id_url.split("/")
        ocal = s_cal[len(s_cal)-2]
        if '_shared_by_' in ocal:
          pos = ocal.find("_shared_by_")
          ocal = ocal[0:pos]
        if not ocal in doc.caldav_id_calendar:
          remove_caldav_event(doc)
          doc.caldav_id_url = None
          doc.event_uid = None
      # Fill CalDav URL with selected CalDav Calendar
      doc.caldav_id_url = doc.caldav_id_calendar
      # Create uid for new events
      str_uid = datetime.datetime.now().strftime("%Y%m%dT%H%M%S")
      uidstamp = 'frappe' + hashlib.md5(str_uid.encode('utf-8')).hexdigest() + '@pibico.es'
      if not doc.event_uid:
        doc.event_uid = uidstamp
      else:
        uidstamp = doc.event_uid
      ucal = str(doc.caldav_id_url).split("/")
      # Get Calendar Name from URL as last portion in URL
      cal_name = ucal[len(ucal)-2]
      # Get CalDav URL, CalDav User and Token
      if fp_user.caldav_url[-1] == "/":
        caldav_url = fp_user.caldav_url + "users/" + fp_user.caldav_username
      else:
        caldav_url = fp_user.caldav_url + "/users/" + fp_user.caldav_username
      caldav_username = fp_user.caldav_username
      caldav_token = get_decrypted_password('User', frappe.session.user, 'caldav_token', False)
      # Set connection to caldav calendar with CalDav user credentials
      caldav_client = caldav.DAVClient(url=caldav_url, username=caldav_username, password=caldav_token)
      cal_principal = caldav_client.principal()
      # Fetching calendars from server
      calendars = cal_principal.calendars()
      if calendars:
        # Loop on CalDav User Calendars to check if event exists
        for c in calendars:
          scal = str(c.url).split("/")
          str_user = scal[len(scal)-3]
          str_cal = scal[len(scal)-2]
          # Check if CalDav calendar name or calendar name shared by another user matches
          if str_cal == cal_name or str_cal + "_shared_by_"  in str(doc.caldav_id_url):
            # Prepare iCalendar Event
            # Initialise iCalendar
            cal = Calendar()
            cal.add('prodid', '-//PibiCal//pibico.org//')
            cal.add('version', '2.0')
            # Initialize Event
            event = Event()
            # Fill data to Event
            # UID  
            event['uid'] = uidstamp
            # SUMMARY from Subject
            event.add('summary', doc.subject)
            # DTSTAMP from current time
            event.add('dtstamp', datetime.datetime.now())
            # DTSTART from start
            dtstart = datetime.datetime.strptime(doc.starts_on, '%Y-%m-%d %H:%M:%S')
            dtstart = datetime.datetime(dtstart.year, dtstart.month, dtstart.day, dtstart.hour, dtstart.minute, dtstart.second, tzinfo=madrid)
            event.add('dtstart', dtstart)
            # DTEND if end
            if doc.ends_on:
              dtend = datetime.datetime.strptime(doc.ends_on, '%Y-%m-%d %H:%M:%S')
              dtend = datetime.datetime(dtend.year, dtend.month, dtend.day, dtend.hour, dtend.minute, dtend.second, tzinfo=madrid)
              event.add('dtend', dtend)
            # DESCRIPTION if any
            if doc.description:
              event.add('description', doc.description)
            # LOCATION if any
            if doc.location:
              event.add('location', doc.location)
            # CATEGORIES from event_category
            category = _(doc.event_category)
            event.add('categories', [category])
            # ORGANIZER from user session
            organizer = vCalAddress(u'mailto:%s' % fp_user)
            organizer.params['cn'] = vText(fp_user.caldav_username)
            organizer.params['ROLE'] = vText('ORGANIZER')
            event.add('organizer', organizer)
            # ATTENDEE if participants
            if doc.event_participants:
              if len(doc.event_participants) > 0:
                for _contact in doc.event_participants:
                  if _contact.reference_doctype in ["Contact", "Customer", "Lead", "Supplier"]:
                    email = frappe.db.get_value("Contact", _contact.reference_docname, "email_id")
                    contact = vCalAddress(u'mailto:%s' % email)
                    contact.params['cn'] = vText(_contact.reference_docname)
                  elif _contact.reference_doctype == "User":
                    contact = vCalAddress(u'mailto:%s' % _contact.reference_docname)
                    contact.params['cn'] = vText(_contact.reference_docname)
                  else:
                    contact = vCalAddress(u'mailto:%s' % "")
                    contact.params['cn'] = vText(_contact.reference_docname)
                  if _contact.participant_type:
                    if _contact.participant_type == "Chairperson":
                      contact.params['ROLE'] = vText('CHAIR') 
                    elif _contact.participant_type == "Required":
                      contact.params['ROLE'] = vText('REQ-PARTICIPANT') 
                    elif _contact.participant_type == "Optional":
                      contact.params['ROLE'] = vText('OPT-PARTICIPANT')
                    elif _contact.participant_type == "Non Participant":
                      contact.params['ROLE'] = vText('NON-PARTICIPANT')
                  else:
                    contact.params['ROLE'] = vText('REQ-PARTICIPANT')
                  if contact:
                    event.add('attendee', contact)
            # Add Recurring events
            if doc.repeat_this_event:
             if doc.repeat_on:
               if not doc.repeat_till:
                 event.add('rrule', {'freq': [doc.repeat_on.lower()]})
               else:
                 dtuntil = datetime.datetime.strptime(doc.repeat_till, '%Y-%m-%d')
                 dtuntil = datetime.datetime(dtuntil.year, dtuntil.month, dtuntil.day, tzinfo=madrid)
                 event.add('rrule', {'freq': [doc.repeat_on.lower()], 'until': [dtuntil]})
            # Add event to iCalendar 
            cal.add_component(event)
            # Save/Update Frappe Event
            c.save_event(cal.to_ical())
            # Get all events in matched calendar just to inform about existing or new event
            all_events = c.events()
            # Loop through events to check if current event exists
            for url_event in all_events:
              cal_url = str(url_event).replace("Event: https://", "https://" + caldav_username + ":" + caldav_token +"@")
              req = requests.get(cal_url)
              cal = Calendar.from_ical(req.text)
              for evento in cal.walk('vevent'):
                if uidstamp in str(evento.decoded('uid')):
                  # print(evento.decoded('summary'), evento.decoded('attendee'), evento.decoded('dtstart'), evento.decoded('dtend'), evento.decoded('dtstamp'))  
                  # Save event in iCalendar to caldav
                  frappe.msgprint(_("Updated/Created Event in Calendar ") + str(c.name))    
                  break
  else:
    if doc.event_uid:
      remove_caldav_event(doc)
      
      doc.caldav_id_url = None
      doc.event_uid = None

@frappe.whitelist()
def remove_caldav_event(doc, method=None):
  if doc.event_uid:
    # Get CalDav Data from logged in user
    fp_user = frappe.get_doc("User", frappe.session.user)
    # Continue if CalDav Data exists on logged in user
    if fp_user.caldav_url and fp_user.caldav_username and fp_user.caldav_token:
      uidstamp = doc.event_uid
      cal_name = None
      if doc.caldav_id_url:
        ucal = str(doc.caldav_id_url).split("/")
        # Get Calendar Name from URL as last portion in URL
        cal_name = ucal[len(ucal)-2]
      # Get CalDav URL, CalDav User and Token
      if fp_user.caldav_url[-1] == "/":
        caldav_url = fp_user.caldav_url + "users/" + fp_user.caldav_username
      else:
        caldav_url = fp_user.caldav_url + "/users/" + fp_user.caldav_username
      caldav_username = fp_user.caldav_username
      caldav_token = get_decrypted_password('User', frappe.session.user, 'caldav_token', False)
      # Set connection to caldav calendar with CalDav user credentials
      caldav_client = caldav.DAVClient(url=caldav_url, username=caldav_username, password=caldav_token)
      cal_principal = caldav_client.principal()
      # Fetching calendars from server
      calendars = cal_principal.calendars()
      doExists = False
      if calendars:
        # Loop on CalDav User Calendars to check if event exists
        for c in calendars:
          scal = str(c.url).split("/")
          str_user = scal[len(scal)-3]
          str_cal = scal[len(scal)-2]
          # Check if CalDav calendar name or calendar name shared by another user matches
          if str_cal == cal_name or str_cal + "_shared_by_"  in str(doc.caldav_id_url):
            # Get all events in matched calendar just to inform about existing or new event
            all_events = c.events()
            # Loop through events to check if current event exists
            for url_event in all_events:
              cal_url = str(url_event).replace("Event: https://", "https://" + caldav_username + ":" + caldav_token +"@")
              req = requests.get(cal_url)
              cal = Calendar.from_ical(req.text)
              for evento in cal.walk('vevent'):
                if uidstamp in str(evento.decoded('uid')):
                  doExists = True
                  break
              if doExists:
                url_event.delete()
                frappe.msgprint(_("Deleted Event in CalDav Calendar ") + str(c.name))
                break