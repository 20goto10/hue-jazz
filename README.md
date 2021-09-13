# hue-jazz
Assorted scripts and tricks for rooted Philips Hue hubs (and some related IOT). 

### Preqrequisites
The stuff here is designed to operate on a rooted Hue hub. You must first
be able to SSH to the Hub. 

* The best instructions for rooting the Hub are located here: 
[Philips Hue 2.1 enabling wifi](https://blog.andreibanaru.ro/2018/03/27/philips-hue-2-1-enabling-wifi/). You can stop after you've got SSH working. (You don't need a wifi adapter for my scripts, and with the latest Hue firmware, the wi-fi steps won't work anymore until someone can compile a working device driver; I'm trying.) Rooting the Hue Hub is fairly simple but cannot be performed without taking apart the unit and having the appropriate tools and a bit of basic hardware-hacking know-how. It would make for a good learning project if you have a spare Hue hub. Prepare to say "eureka!" if you've never done this sort of thing before. If you're into this sort of thing it may become addictive. (By the way, I didn't use a soldering iron, I just stuck the serial connection wires in and made sure not to jiggle anything once I got the console and shorted the flash chip as instructed.) The unit seems fairly resilient but please do not blame me if you brick it.

* Micropython is required, but it's already on the Hue, at least in the current firmware (version 1946157000). You don't really need much coding skill to work with these scripts. 

* For the bulb_sync script you also need [rgbxy](https://github.com/benknight/hue-python-rgb-converter/). Whereever you put this script, you can just create a subdir called rgbxy and put that repo's \_\_init\_\_.py in it. 

* You will also probably need curl or wget on your Hue. I don't remember whether either one is on the Hue already, but they can be added via opkg (see [this article](https://medium.com/@rxseger/enabling-the-hidden-wi-fi-radio-on-the-philips-hue-bridge-2-0-42949f0154e1) for instructions on getting opkg running). 

* You can scp the script(s) to the hub, or just open up your text editor and paste it straight in from the clipboard.

* You will want to customize the settings toward the top of the script, obviously, then test with the simple: ```/usr/bin/micropython name_of_script.py```

* After you've tested your customizations, you can edit ```/etc/rc.local``` and add it to startup above the ```exit 0``` line:

* When it is all working and you want the Hue to automatically start your script, assuming you used bulb_sync.py and put in /root, just use:

```/usr/bin/micropython /root/bulb_sync.py &```

### What's here:

* **bulb_sync.py**: control a non-Hue bulb by updating another bulb with the conversion from its XY+brightness color to the HSV/HSB values needed in OpenHab (and probably other HA tools). This script monitors the queue for the change messages from a specific bulb, which means you can have multiple non-Hue lights do the same thing as any Hue bulb (triggered by the app or sensor), and when you use the dimmer the non-Hue lights will follow the same instructions with minimal latency. There's also optional code for a pointless color shift on the non-Hue bulb(s), i.e. silly lighting effects.

* **hue_mqtt_listener.py**: listen for specific sensor (dimmer) events and act on them. Can be combined with bulb_sync but doesn't require color conversion. This script takes a map of button commands and executes whatever arbitrary request you have in the map, most likely a curl command.

* Personally I have both scripts merged together for my purposes, but you can also just run both simultaneously if you need them.

### Background
My work began with the Hue dimmer switch and Openhab rules files. Here is my old, [very obsolete article](https://www.benchadwick.com/2018/12/using-a-hue-dimmer-switch-on-non-hue-devices-with-openhab2/) on how to make the switches work with OpenHab via the existing addon, but note that it has far higher latency than what you get through this hacked-Hue method.

My apartment doesn't have enough light switches, so IOT lights and wireless dimmers have given me a great deal of flexibility. The Hue dimmer is the best and cheapest solution for the switch problem, given that I cannot easily carve into the walls to rewire the place (and shouldn't have to, with IOT lights). 

The Hue Dimmer (especially the first version) is designed to adhere to walls (with tape or built-in magnets). I have not been able to find any affordable alternative that is as good for my needs, and Hue bulbs are expensive, so I've found ways to adapt the switch to control non-Hue lights through OpenHAB. 

The drawback of the OpenHAB rules-based approach described in my older article is that it must poll the Hue API for the state of the dimmers, which is not 100% reliable, since (for example) repeated button presses may be skipped, and which introduces additional latency (to what is already a flaky enough system due to wi-fi dropouts, a problem with the cheaper bulbs themselves).

The scripts here run on a rooted Hub itself and listen for the original signals coming over MQTT, which is as close as we can get to them. This means the dimmer can be a direct push trigger to whichever home automation software is in use (OpenHAB in my case; depending on the bulb and your network config, you could also send a request to its own API).

Dear Philips, love the products. Please never lock them down as a result of the six or seven people who will bother rooting the thing.
 
### Work in progress:
* improvements to the above scripts. Ideally they should load configuration from a separate file so no changes would be necessary to the main script. 
* attempts to insert a "virtual" light bulb or sensor that would be treated as real by the Hue app and API.
* attempts to restore the ath9k (or other?) driver for activating the built-in wireless unit. I was able to build the drivers for the kernel, but they still do not spot the chip (unlike in earlier versions of the Hue SOC).
* virtual "scenes" - a way to convince the unit to use non-Hue bulbs as parts of scenes.
* user-suggested tweaks

### Philosophies behind this work (in case you care):
* I bought a thing. I own it. I should be able to do whatever I want with it (if it doesn't harm anyone else)... Root access should be considered a right.
* The recent model of having in-home units make API calls to distant servers to control things in the home is idiotic. (Guilty: all Tuya/SmartHome products and pretty much all the other discount companies.) There may be exceptions for people who need to control stuff when they aren't home, but that should be the exception, not the standard. The only time I want my devices reaching out is when there are firmware upgrades and even then I want to know exactly what is changing, before it kicks in. So I'm trying to lock down all my IOT devices to never make outside calls without me knowing. In the case of the cheap stuff, I recommend flashing with Tasmota wherever possible. As that is become increasingly un-possible, I'm looking into other approaches.
* For environmental reasons and simple matters of sanity, Hue really needs to stop bundling extraneous Hubs in with the multi-packs. However the extra Hubs were an unexpected benefit this time around-- I now have three Hubs to experiment with... one rooted and stuck on the old firmware, one rooted with the new firmware, and one I haven't even pulled out of the sleeve.
