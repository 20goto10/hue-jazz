#!/usr/bin/env python3
# hue_mqtt_monitor.py -- from http://github.com/20goto10/hue-jazz
#
# Trigger whatever requests you like (presumably to an alternate server) from a dimmer switch or other sensor.
# It is designed to run on a rooted Hue using micropython.
#
# This software uses the Carl Perkins License, (C) 1955:
# Do anything that you want to do, but don't you step on my blue suede shoes.

import json
import uasyncio as asyncio
from mqtt import Mqtt
import sys
import zlib
import os
import math

VERSION = "0.00000001"

# SETTINGS:
# Settings that you may need to modify. 
# At some point I will have this load from a separate JSON file.

# debug options: have it print messages for all the stuff it ignores, or all the stuff that it actually matches.
# I ship this with debugging on because you need some info from the MQTT messages, but once it's working you'll want this off.
print_skipped_messages = False
print_matched_messages = True
print_commands = False

# This is set up for Openhab, but it could be anything you want that has a reachable API... or fire off some other command altogether.
openhab_url = "http://mylightcontroller:8080/"
curl_command = "/usr/bin/curl"

def curl_req_for(target, command):
  return curl_command + " " + openhab_url + "rest/items/" + target + " -H 'Content-Type: text/plain' --data-raw " + command

# Map of requests (in my format) to actions. The /sensors/id can be derived from the debug output. Each dimmer has four buttons, 1-4.
# The types of presses are initial_press, short_release, long_release, repeat. 'repeat' seems to show up for long_release only and I'm not sure what it really means.
# The key is the request fields for the sensor ID, button press type, and button # on the dimmer, delineated by colons.
action_map = {
              # example: map top and bottom to on/off for some group, middle buttons on/off for some light
              "/sensors/49:short_release:1": curl_req_for("LivingRoom", "ON"),
              "/sensors/49:short_release:2": curl_req_for("Light1", "ON"),
              "/sensors/49:short_release:3": curl_req_for("Light1", "OFF"),
              "/sensors/49:short_release:4": curl_req_for("LivingRoom", "OFF"),

              # example: have different effects on long-press on a different dimmre
              "/sensors/50:short_release:1": curl_req_for("ColLivRoomLights", "ON"),
              "/sensors/50:short_release:2": curl_req_for("CouchLight", "ON"),
              "/sensors/50:long_release:2":  curl_req_for("StageLight", "ON"),
              "/sensors/50:short_release:3": curl_req_for("CouchLight", "OFF"),
              "/sensors/50:long_release:3":  curl_req_for("StageLight", "OFF"),
              "/sensors/50:short_release:4": curl_req_for("ColLivRoomLights", "OFF"),

              # example: an arbitrary curl request to some outside API (i.e. control some Tuya/SmartHome/Govee/whatever unsupported by OpenHab)
              "/sensors/14:short_release:1": "curl --insecure --location --request PUT 'https://some-random-tuya-api-or-whatever' --header 'My-API-Key: blahblah' -- developer-api.doyoureallytrustthissystem.com/v1/devices/control' 'Content-Type: application/json' --data-raw '{\"device\": \"AA:BB:A4:C1:38:FD:F0:ED\",\"model\": \"H6143\",\"cmd\": {\"name\": \"turn\", \"value\": \"on\"}}'",
              "/sensors/14:short_release:4": "curl --insecure --location --request PUT 'https://some-random-tuya-api-or-whatever' --header 'My-API-Key: blahblah' -- developer-api.doyoureallytrustthissystem.com/v1/devices/control' 'Content-Type: application/json' --data-raw '{\"device\": \"AA:BB:A4:C1:38:FD:F0:ED\",\"model\": \"H6143\",\"cmd\": {\"name\": \"turn\", \"value\": \"on\"}}'",
             }
# END SETTINGS

async def data_listener(topic, mqtt):
    async for msg in mqtt.subscribe(topic):
        handle_data_message(topic, msg)                          
                  
async def main():
    async with Mqtt("pymosquitto") as m:
        tasks = []                                     
        tasks.append(asyncio.create_task(data_listener("dt/clip/+/+",m)))
        await asyncio.gather(*tasks)

def handle_data_message(topic, msg):
      item = json.loads(zlib.decompress(msg["payload"], -15).decode())
          
      cmd_list = []
      if "button" in item:  # this might be something else for different sensor types -- I don't have any.
        cmd = ""
        request = item["id_v1"] + ":" + item["button"]["last_event"] + ":" + str(item["metadata"]["control_id"])

        if request in action_map:
          cmd_list.append(action_map[request])

        if print_matched_messages:
          print(request) # use this to easily map as-yet unmapped buttons
      else:
        if print_skipped_messages:
          print(topic, json.dumps(item, indent=2)) # you may want to remove the "indent" option to save screen space

      # execute the commands 
      for cmd in cmd_list:
        if print_commands:
          print("* Issuing command: " + cmd)
        os.system(cmd)

      sys.stdout.flush()

asyncio.run(main())
asyncio.get_event_loop().run_forever()

