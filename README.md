# hue-jazz
Assorted scripts and tricks for rooted Philips Hue hubs (and some related IOT). 

### Preqrequisites
The stuff here is designed to operate on a rooted Hue hub. You must first
be able to SSH to the Hub. Instructions for rooting the unit are located elsewhere. 

### Background
My work began with the Hue dimmer switch (here is my old, very obsolete article on how to make it work with OpenHab).

My apartment doesn't have enough light switches, so IOT lights and wireless dimmers have given me a great deal of flexibility. The Hue dimmer is the best and cheapest solution for the switch problem, given that I cannot easily carve into the walls to rewire the place (and shouldn't have to, with IOT lights). 

The Hue Dimmer (especially the first version) is designed to adhere to walls (with tape or built-in magnets). I have not been able to find any affordable alternative that is as good for my needs, and Hue bulbs are expensive, so I've found ways to adapt the switch to control non-Hue lights through OpenHAB. 

The drawback of the OpenHAB rules-based approach described in my older article is that it must poll the Hue API for the state of the dimmers, which is not 100% reliable, since (for example) repeated button presses may be skipped, and which introduces additional latency (to what is already a flaky enough system due to wi-fi dropouts, a problem with the cheaper bulbs themselves).

My newer work runs on a rooted Hub itself and listens for the original signals coming in, or at least, the MQTT messages that are as close as we can get to them. This means the dimmer can be a direct push trigger to whichever home automation software is in use (OpenHAB in my case; depending on the bulb and your network config, you could also send a request to its own API).

### What's here:
A handful of scripts, for now:
* dimmer_duper: control a non-Hue bulb with the Hue dimmer by updating another bulb with the conversion from its XY+brightness color to the HSV/HSB values needed in OpenHab (and probably other HA tools). 
* hue_zigbee_monitor: listen for specific sensor (dimmer) events and act on them
* monitor_everything: watch ALL the MQTT input/output from the Hue
* old_scripts: some stuff I generated in my research that I do not recommend using.
 
### Work in progress:
* improvements to the above scripts. Right now they have a lot of dumb "if" statements and ideally they would load configuration from a separate file so no changes would be necessary to the main script.
* attempts to insert a "virtual" light bulb or sensor that would be treated as real by the Hue app and API.
* attempts to restore the ath9k (or other?) driver for activating the built-in wireless unit. I was able to build the drivers for the kernel, but they still do not spot the chip (unlike in earlier versions of the Hue SOC).
* virtual "scenes" - a way to convince the unit to use non-Hue bulbs as parts of scenes.

### Philosophies behind this work (in case you care):
* I bought a thing. I own it. I should be able to do whatever I want with it (if it doesn't harm anyone else)... Root access should be considered a right.
* The recent model of having in-home units make API calls to distant servers to control things in the home is idiotic. (Guilty: all Tuya/SmartHome products and pretty much all the other discount companies.) There may be exceptions for people who need to control stuff when they aren't home, but that should be the exception, not the standard. The only time I want my devices reaching out is when there are firmware upgrades and even then I want to know exactly what is changing, before it kicks in. So I'm trying to lock down all my IOT devices to never make outside calls without me knowing. In the case of the cheap stuff, I recommend flashing with Tasmota wherever possible. As that is become increasingly un-possible, I'm looking into other approaches.
* For environmental reasons and simple matters of sanity, Hue really needs to lower the price point on the lights and stop bundling extraneous Hubs in with the multi-packs. However the extra Hubs were an unexpected benefit this time around-- I now have three Hubs to experiment with... one rooted and stuck on the old firmware, one rooted with the new firmware, and one I haven't even pulled out of the sleeve.
