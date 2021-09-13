#!/usr/bin/env python3
# bulb_sync.py -- from http://github.com/20goto10/hue-jazz
#
# Monitors a bulb for changes. You can use this to (fairly) easily tie a single Hue bulb with n non-Hue bulbs, so that
# all of them change in tandem (triggered by a dimmer, the app, or whatever).
# Requires: rgbxy, 
#   available here: https://github.com/benknight/hue-python-rgb-converter/ courtesy of Benjamin Knight.
#   You can just create a subdirectory called rgbxy and put that one __init__.py file in it.
#
# This is designed to be run on a rooted Hue with micropython.
#
# This software uses the Carl Perkins License, (C) 1955:
# Do anything that you want to do, but don't you step on my blue suede shoes.
#

import json
import uasyncio as asyncio
from rgbxy import *
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
print_skipped_messages = True
print_matched_messages = True
print_commands = True

# The source bulb's name in text (as saved in the Hue). This arrives in the
# metadata for the message. You must set this correctly or you won't see 
# any output. Easy to discover by setting debug to True.
name_of_bulb_to_monitor = "Dining room sconce hue"

# Specify the Hue bulb's color Gamut here, identified as GamutA, GamutB, or GamutC.
# This can be determined by inspecting the bulb's status messages (and 
# and is probably tied to the model). My bulbs all use Gamut C so I'm not
# sure.  It's probably not a major issue if you have this wrong, it just 
# means your synced lights' colors won't line up as perfectly.
converter = Converter(GamutC)

# target bulb root of command. You will want to do some tailoring here. This should work on Openhab when you set it correctly.
# Other HA apps use similar but different APIs.
target_bulbs = ["DiningHand"] # I doubt your bulb is also called "DiningHand"... you can add additional bulbs to this list.
# You can also trigger a cycling effect, if you want it, by including the Hue bulb (in Openhab) with a color shift, and changing
# color_shift to True, below, and having a number_of_colors value different from the actual number of bulbs.

# Should be noted, these don't actually need to be bulbs, unless you are writing a curl request to the actual item itself. 
# Otherwise, you don't need to list every bulb as a target, unless you want to use the color shift effect. 
# Otherwise just use a group/room/whatever in your home automation software and address the request to that. 
openhab_url = "http://192.168.1.120:8080/"
target_bulb_cmd_prefixes = []
for bulb in target_bulbs:
  target_bulb_cmd_prefixes.append("/usr/bin/curl " + openhab_url + "rest/items/" + bulb + " -H 'Content-Type: text/plain' --data-raw")

# Optional effect to have the lights at alternate color wheel points, for balance or psychedelia or whatever. Included for silly fun.
# As written, each bulb in the list will be one more step along the phase. 
color_shift = True
phase_shift_angle = 60 

# END SETTINGS

async def data_listener(topic, mqtt):
    async for msg in mqtt.subscribe(topic):
        handle_data_message(topic, msg)                          
                  
async def main():
    async with Mqtt("pymosquitto") as m:
        tasks = []                                     
        tasks.append(asyncio.create_task(data_listener("dt/clip/+/+",m)))
        await asyncio.gather(*tasks)


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
      item = json.loads(zlib.decompress(msg["payload"], -15).decode())
          
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

