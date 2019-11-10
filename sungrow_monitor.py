#!/usr/bin/env python

# Copyright (c) 2019 Thomas Fairbank
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

from pymodbus.payload import BinaryPayloadDecoder
from pymodbus.constants import Endian
from pymodbus.client.sync import ModbusTcpClient
from pytz import timezone
import logging
import config
import json
import time
import datetime
import requests
import traceback
import pathlib
import csv
from astral import Location

MIN_SIGNED   = -2147483648
MAX_UNSIGNED =  4294967295

print("Load config for inverter: %s" % config.inverter_ip)
print("Timezone is %s" % config.timezone)
print("The current time is %s" % (datetime.datetime.now(timezone(config.timezone))).strftime("%Y-%m-%d %X"))

# setup the location for to determine dawn/dusk
l = Location()
l.name = config.location
l.region = 'region'
l.latitude = config.latitude
l.longitude = config.longitude
l.timezone = config.timezone
l.elevation = config.elevation

# modbus datatypes and register lengths
sungrow_moddatatype = {
  'S16':1,
  'U16':1,
  'S32':2,
  'U32':2,
  'STR16':8
  }

# Load the modbus map from config
configfile = "/config/" + config.modbus_file
if pathlib.Path(configfile).is_file():
  modmap = __import__(configfile)
  print("Importing modbusmap from /config" )
else:
  modmap = __import__(config.modbus_file)
  print("importing default modbusmap")
print("Load ModbusTcpClient")

client = ModbusTcpClient(config.inverter_ip, 
                         timeout=config.timeout,
                         RetryOnEmpty=True,
                         retries=3,
					               ZeroMode=True,
                         port=config.inverter_port)

inverter = {}
power_gen = []
power_con = []
voltage_1 = []
voltage_2 = []
#if upload_consumption hasn't been defined in the config, then assume false. If its explicitly false let it be that, otherwise its true
try:
	config.upload_consumption
except AttributeError:
	upload = False
else:
	upload = config.upload_consumption
bus = json.loads(modmap.scan)

def load_register(registers):
  from pymodbus.payload import BinaryPayloadDecoder
  from pymodbus.constants import Endian

  #moved connect to here so it reconnect after a failure
  client.connect()
  #iterate through each avaialble register in the modbus map
  for thisrow in registers:
    name = thisrow[0]
    startPos = thisrow[1]-1 #offset starPos by 1 as zeromode = true seems to do nothing for client
    data_type = thisrow[2]
    format = thisrow[3]
   
    #try and read but handle exception if fails
    try:
      received = client.read_input_registers(address=startPos,
                                             count=sungrow_moddatatype[data_type],
                                              unit=config.slave)
    except:
      thisdate = str(datetime.datetime.now(timezone(config.timezone))).partition('.')[0]
      thiserrormessage = thisdate + ': Connection not possible. Check settings or connection.'
      print(thiserrormessage)
      return
    
    #Add timestamp based on PC time rather than inverter time
    inverter["Date"] = datetime.datetime.now(timezone(config.timezone)).strftime("%Y-%m-%d")
    inverter["Timestamp"] = datetime.datetime.now(timezone(config.timezone)).strftime("%X")
    
    # 32bit double word data is encoded in Endian.Little, all byte data is in Endian.Big
    if '32' in data_type:
        message = BinaryPayloadDecoder.fromRegisters(received.registers, byteorder=Endian.Big, wordorder=Endian.Little)
    else:
        message = BinaryPayloadDecoder.fromRegisters(received.registers, byteorder=Endian.Big, wordorder=Endian.Big)
    #decode correctly depending on the defined datatype in the modbus map
    if data_type == 'S32':
      interpreted = message.decode_32bit_int()
    elif data_type == 'U32':
      interpreted = message.decode_32bit_uint()
    elif data_type == 'U64':
      interpreted = message.decode_64bit_uint()
    elif data_type == 'STR16':
      interpreted = message.decode_string(16).rstrip('\x00')
    elif data_type == 'STR32':
      interpreted = message.decode_string(32).rstrip('\x00')
    elif data_type == 'S16':
      interpreted = message.decode_16bit_int()
    elif data_type == 'U16':
      interpreted = message.decode_16bit_uint()
    else: #if no data type is defined do raw interpretation of the delivered data
      interpreted = message.decode_16bit_uint()
    
    #check for "None" data before doing anything else
    if ((interpreted == MIN_SIGNED) or (interpreted == MAX_UNSIGNED)):
      displaydata = None
    else:
      #put the data with correct formatting into the data table
      if format == 'FIX3':
        displaydata = float(interpreted) / 1000
      elif format == 'FIX2':
        displaydata = float(interpreted) / 100
      elif format == 'FIX1':
        displaydata = float(interpreted) / 10
      else:
        displaydata = interpreted
    
    inverter[name] = displaydata


#define a loop timer that can account for drift to keep upload in sync
def loop_timer(delay, task):
  next_time = time.time() + delay
  while True:
    time.sleep(max(0, next_time - time.time()))
    try:
      task()
    except Exception:
      traceback.print_exc()
      # in production code you might want to have this instead of course:
      # logger.exception("Problem while executing repetitive task.")
    # skip tasks if we are behind schedule:
    next_time += (time.time() - next_time) // delay * delay + delay

#dumb loop counter to trigger send
count=0
    
#main program loop
def main():
  now = datetime.datetime.time(datetime.datetime.now(timezone(config.timezone)))
  if (now > l.sun()['dawn'].time() or now > l.sun()['dusk'].time()):
      logging.debug("Its night time, I'm going to sleep")
  else:
    global count
    try:
      global inverter
      inverter = {}
      load_register(modmap.sungrow_registers)
      if len(inverter) > 0: #only continue if we get a successful read
        #TODO: functionize this block as its jus the same check for each register with different safe LT value
        if inverter["5031 - Total active power"] <90000: #sometimes the modbus give back a weird value
          power_gen.append(inverter["5031 - Total active power"])
          logging.debug("Total active power = %s" % inverter["5031 - Total active power"])
        else:
          logging.debug("Didn't get a read for Total Active Power")
        if inverter["5011 - MPPT 1 voltage"] <9000: #sometimes the modbus give back a weird value
          voltage_1.append(inverter["5011 - MPPT 1 voltage"])
          logging.debug("MPPT 1 Voltage = %s" % inverter["5011 - MPPT 1 voltage"])
        else:
          logging.debug("Didn't get a read for MPPT 1 Voltage")
        if inverter["5013 - MPPT 2 voltage"] <9000: #sometimes the modbus give back a weird value
          voltage_2.append(inverter["5013 - MPPT 2 voltage"])
          logging.debug("MPPT 2 Voltage = %s" % inverter["5013 - MPPT 2 voltage"])
        else:
          logging.debug("Didn't get a read for MPPT 2 Voltage")
        #if config has elected to upload consumption data then we should store those registers if they are enabled
        if upload:
          if inverter["5097 - Daily import energy"] <50000: #sometimes the modbus give back a weird value
            power_con.append(inverter["5097 - Daily import energy"])
            logging.debug("Daily import energy = %s" % inverter["5097 - Daily import energy"])
          else: 
            logging.debug("Didn't get a read for Daily Import Energy")
        #log to csv all read values
        if not pathlib.Path("/config/" + inverter["Date"] + "_reads.csv").is_file():
          with open("/config/" + inverter["Date"] + "_reads.csv", "a", newline='\n', encoding='utf-8') as fp:
              wr = csv.writer(fp, dialect='excel')
              wr.writerow(inverter.keys())
              wr.writerow(inverter.values())
        else:
          with open("/config/" + inverter["Date"] + "_reads.csv", "a", newline='\n', encoding='utf-8') as fp:
              wr = csv.writer(fp, dialect='excel')
              wr.writerow(inverter.values())
        # we are done with the connection for now so close it
      client.close()
    except Exception as err:
      print("[ERROR] %s" % err)
      client.close()
    #increment counter
    count+=1
    if count >= (60/config.scan_interval) * config.upload_interval and len(power_gen) >= 1 : #possibly spawn thread here and instead make counter be every 5 mins
      print("%d individual observations were made (out of %d attempts) over the last %d minutes averaging %d Watts" % (len(power_gen), count, count*config.scan_interval/60,sum(power_gen)/len(power_gen)))
      count = 0
      now = datetime.datetime.now(timezone(config.timezone))
      try: 
        v6 = inverter["5019 - Phase A voltage"]
        if upload:
          querystring = {"d":"%s" % now.strftime("%Y%m%d"),"t":"%s" % now.strftime("%H:%M"),"v2":"%s" % (sum(power_gen)/len(power_gen)), "v4":"%s" % (sum(power_con)/len(power_con)) ,"v6":"%s" % v6}
        else:
          querystring = {"d":"%s" % now.strftime("%Y%m%d"),"t":"%s" % now.strftime("%H:%M"),"v2":"%s" % (sum(power_gen)/len(power_gen)), "v6":"%s" % v6}
          
        #wipe the array for next run
        del power_gen[:]
        del voltage_1[:]
        del voltage_2[:]
        del v6
        del power_con[:]
        headers = {
          'X-Pvoutput-Apikey': "%s" % config.pv_api,
          'X-Pvoutput-SystemId': "%s" %config.pv_sid,
          'Content-Type': "application/x-www-form-urlencoded",
          'cache-control': "no-cache"
        }
        response = requests.request("POST", url=config.pv_url, headers=headers, params=querystring)
        if response.status_code != requests.codes.ok:
            print ("!!!Upload failed!!!\nError: %s" % response.text)
        else:
            logging.debug("Successfully posted to %s" % config.pv_url)
      except Exception as err:
        print("[ERROR] %s" % err)
    #sleep until next iteration
    logging.debug("Loop %d of %d complete. Sleeping %ds...." % (count, (60/config.scan_interval)*config.upload_interval, config.scan_interval))

loop_timer(config.scan_interval, main)

