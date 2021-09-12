#!/bin/sh
# This simple script does not require a rooted Hue but it does require
# jsonfilter, which is *on* the Hub, and does not seem to be the same
# project that exists on Github. I think the right one is available via opkg 
# for other, similar SOC devices.
#
# This script polls OpenHab every 1 second for the status of one bulb and uses
# it to update another bulb. Consider it the first draft of the faster,
# better, rooted-Hue only micropython script available at the hue-jazz repo.
#
# Find more info at: github.com/20goto10/hue-jazz
#
# It is also probably possible to do this through OpenHab itself, so 
# basically, I don't think there is any real audience for this script.
# "jq" can do the same thing as "jsonfilter" if you do need this.

### Parameters to set yourself:

OPENHAB_URL=http://whatever:8080 # update this to your OpenHAB url
HUE_API_KEY=some_key # you get this key by registering a user through the API (i.e. after pressing the button on the Hue)
HUE_API_URL=http://localhost # the IP address of the Hue Hub, or "http://localhost" if you are running this on the Hue itself

# Hue API ID for the light being tracked
TRACKED_BULB_ID=/lights/5

# Openhab URL of the light being updated
UPDATED_BULB_URL=${OPENHAB_URL}/rest/items/MyNotHueBulb

### 

while true
  do
    # state is written to a temp file b/c I could not get  
    # jsonfilter to work correctly on the simple string (quote escape
    # issues not worth figuring out)
    tfile="/tmp/curled_insta_state"
    echo curl -s ${HUE_API_URL}/api/${HUE_API_KEY}/${TRACKED_BULB_ID}
    curl -s ${HUE_API_URL}/api/${HUE_API_KEY}/${TRACKED_BULB_ID} > $tfile

#    echo `cat $tfile`
    hue=$(jsonfilter -i $tfile -e '@["state"]["hue"]')
    sat=$(jsonfilter -i $tfile -e '@["state"]["sat"]')
    bri=$(jsonfilter -i $tfile -e '@["state"]["bri"]')

    newhue=$(expr $hue / 182)
    newsat=$(expr $sat \* 100 / 255)
    newbri=$(expr $bri \* 100 / 255)
    result="$newhue,$newsat,$newbri"
    # echo curl $UPDATED_BULB_URL -H 'Content-Type: text/plain' --data-raw $result 
    curl $UPDATED_BULB_URL -H 'Content-Type: text/plain' --data-raw $result 
    sleep 1
  done

