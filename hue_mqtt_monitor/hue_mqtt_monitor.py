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

VERSION = "0.00000002"

# SETTINGS:
# Settings that you may need to modify. 
# At some point I will have this load from a separate JSON file.

# debug options: have it print messages for all the stuff it ignores, or all the stuff that it actually matches.
# I ship this with debugging on because you need some info from the MQTT messages, but once it's working you'll want this off.
print_everything = True
print_skipped_messages = False 
print_matched_messages = True
print_commands = True 

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
              "/sensors/14:short_release:1": "curl --insecure --location --request PUT 'https://some-random-tuya-api-or-whatever' --header 'My-API-Key: blahblah' -- developer-api.doyoureallytrustthissystem.com/v1/devices/control' 'Content-Type: application/json' --data-raw '{\"device\": \"AA:BB:CC:DD:EE:FF:11:22\",\"model\": \"Banana\",\"cmd\": {\"name\": \"turn\", \"value\": \"on\"}}'",
              "/sensors/14:short_release:4": "curl --insecure --location --request PUT 'https://some-random-tuya-api-or-whatever' --header 'My-API-Key: blahblah' -- developer-api.doyoureallytrustthissystem.com/v1/devices/control' 'Content-Type: application/json' --data-raw '{\"device\": \"AA:BB:CC:DD:EE:FF:11:22\",\"model\": \"Banana\",\"cmd\": {\"name\": \"turn\", \"value\": \"off\"}}'",
             }
# END SETTINGS

device_map = {}

async def device_listener(mqtt):
    topic = "dt/clip/device/+"
    async for msg in mqtt.subscribe(topic):
        handle_sensor(topic, msg)

async def data_listener(topic, mqtt):
    async for msg in mqtt.subscribe(topic):
        handle_data_message(topic, msg)
                  
async def main():
    async with Mqtt("pymosquitto") as m:
        tasks = []                                     
        tasks.append(asyncio.create_task(device_listener(m)))
        tasks.append(asyncio.create_task(data_listener("cmd/clip/event/publish",m)))
        await asyncio.gather(*tasks)


def handle_sensor(topic, msg):
   try:
      item = json.loads(zlib.decompress(msg["payload"], -15).decode())
      if print_everything:
        print("device found", topic, item)
      if item["product_data"]["product_name"] == "Hue dimmer switch":
        if "services" in item:
          bulbs = item["services"]
          counter = 1 
          for service in bulbs:
            if service["rtype"] == "button":
              if print_everything:
                print("Adding", service["rtype"], service["rid"])
              device_map[service["rid"]] = str(counter)
              counter = counter + 1
   except Exception as e: 
      print("handle_sensor error:", str(e))

def rgb_to_hsv(r, g, b):
    maxc = max(r, g, b)
    minc = min(r, g, b)
    v = maxc
    if minc == maxc:
        return 0.0, 0.0, v
    s = (maxc-minc) / maxc
    rc = (maxc-r) / (maxc-minc)
    gc = (maxc-g) / (maxc-minc)
    bc = (maxc-b) / (maxc-minc)
    if r == maxc:
        h = bc-gc
    elif g == maxc:
        h = 2.0+rc-bc
    else:
        h = 4.0+gc-rc
    h = (h/6.0) % 1.0
    return h, s, v


def handle_data_message(topic, msg):
   try:
      item = json.loads(msg["payload"].decode())

      if print_everything:
        print(item)
          
      cmd_list = []


      # your handler stuff goes here -- one would probably want it to be a bit more sophisticated, but this is just a POC
      if "metadata" in item and "name" in item["metadata"]:
        if item["metadata"]["name"] == name_of_bulb_to_monitor:
          if print_matched_messages:
            print(topic, json.dumps(item, indent=2)) # you may want to remove the "indent" option to save screen space

          if "color" in item:
            # get color info from the reported changes 
            colors = item["color"]["xy"]
            bri = item["dimming"]["brightness"]
            bri_s = str(int(bri))
            is_on = item["on"]["on"] # not a typo

            # there's probably a way to go from XY straight to HSB, 
            # but eh, we're in no rush
            r,g,b = converter.xy_to_rgb(colors["x"], colors["y"], bri)
            h,s,v = rgb_to_hsv(r,g,b)
            h = h * 360.0 
            s = s * 100.0

            for cmd_prefix in target_bulb_cmd_prefixes:
              if color_shift:
                h = (int (h + phase_shift_angle)) % 360  
              if not is_on:
                color_string = "OFF" # sending any colors will trigger OpenHAB to turn it on, but Hue treats color and on/off independently, so this forces it to recognize on/off
              else:
                color_string = str(int(h)) + ","  + str(int(s)) + "," + bri_s
              cmd = cmd_prefix + " " + color_string
              cmd_list.append(cmd)

      # sensor button handling
      elif "data" in item and "button" in item["data"][0]["data"][0]:
        id_v1 = item["data"][0]["data"][0]["id_v1"]
        last_event = item["data"][0]["data"][0]["button"]["last_event"]
        control_id = device_map[item["data"][0]["data"][0]["id"]]
        request = id_v1 + ":" + last_event + ":" + control_id

        if request in action_map:
          cmd_list.append(action_map[request])

        if print_matched_messages:
          print(request) # use this to easily map as-yet unmapped buttons
        
      else:
        if print_skipped_messages:
          print(topic, json.dumps(item, indent=2)) # you may want to remove the "indent" option to save screen space

      # execute the commands 
      for cmd in flatten(cmd_list):
        if print_commands:
          print("* Issuing command: %s" % cmd)
        try:
          os.system(cmd)
        except:
          print("* Command failed %s" % cmd)
      sys.stdout.flush()
   except Exception as e: 
      print("Execution failure", str(e))

asyncio.run(main())
asyncio.get_event_loop().run_forever()


