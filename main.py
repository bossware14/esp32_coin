import usocket
import json
import network
import machine
import time
from wifi_manager import WifiManager
import ubinascii
import math
import urequests
import coin
import os

serial_no = ubinascii.hexlify(machine.unique_id()).decode('utf-8').upper()
print("serial_no:",serial_no)

wm = WifiManager()
wm.connect()
checkCnnect = 0

while True:
    if wm.is_connected():
        print('Connected!')
        break
    else:
        if checkCnnect >= 5:
            os.remove('wifi.dat')
            print('ReConnect Wifi!')
            time.sleep(1)
            machine.reset()
        print('Disconnected!')
        checkCnnect = checkCnnect + 1
        wm.connect()
        time.sleep(2)

ap_if = network.WLAN(network.WLAN.IF_AP)
ip_address = ap_if.ipconfig('addr4')

def newWriteFile(file,data) :
    f = open(file,'w') 
    f.write(data) 
    f.close()
    
def readFile(file,type) :
    f = open(file) 
    data = f.read()
    f.close()
    if type == 'json' :
        data = json.loads(data)
    return data

def getVersion():
    print('CheckVersion')   
    headers = {'content-type':'application/json'}
    url = 'https://esp32-th-default-rtdb.asia-southeast1.firebasedatabase.app/version.json'
    response = urequests.get(url,headers=headers)
    res = response.json()
    json_data = json.dumps(res)
    version = readFile('version.json','')
    response.close()
    print("Version:",version)
    if json_data != version :
        newWriteFile('version.json',json_data.encode())
        return getConfig(1)
    
def getConfig(update) :
    headers = {'content-type':'application/json'}
    url = 'https://esp32-th-default-rtdb.asia-southeast1.firebasedatabase.app/config.json'
    response = urequests.get(url,headers=headers)
    res = response.json()
    json_data = json.dumps(res)
    response.close()
    if update == 1 :
            print("UPDATE VERSION")
            newWriteFile('config.json',json_data.encode())
            print("Reboot..")
            time.sleep(5)
            machine.reset()
    else: 
        return json_data
    
getVersion()
time.sleep(1)

try:
    config = readFile('config.json', 'json')
    print(config)
except Exception as e:
    print(f"Error reading config.json: {e}")
    config = getConfig(0)
    print(config)


if config['sendcoin'] == 1:
    try:
        coin.bill_pulse_count = coin.readCoin()
        coin.bill_last_state = 0
        coin.total = coin.readCoin()
    except Exception as e:
        print(f"Error reading coin data: {e}")
        coin.bill_pulse_count = 0
        coin.bill_last_state = 0
        coin.total = 0


try:
    pin_coin = machine.Pin(config['gpio'], machine.Pin.IN)
    pin_coin.irq(trigger=machine.Pin.IRQ_RISING, handler=coin.coin_callback)
    print("GPIO",config['gpio'])
except Exception as e:
    pin_coin = machine.Pin(14, machine.Pin.IN)
    pin_coin.irq(trigger=machine.Pin.IRQ_RISING, handler=coin.coin_callback)
    print("GPIO_14")
    
led = machine.Pin(2, machine.Pin.OUT)
led.value(1)
pwm = machine.Pin(4, machine.Pin.OUT)
pwm.value(0)
def putdata(coin):
    headers = {'content-type':'application/json'}
    data = {"time":time.time(),"coin":coin,"online":"1","sending":0,"wifi":wm.get_address(),"server":ip_address,"localtime":time.localtime()}
    url = config['url']+str(serial_no)+'.json'
    try:
        response = urequests.put(url,json=data,headers=headers)
        print(response.json())
    except Exception as e:
        print(f"Error putting data: {e}")

def updateOnline():
    url = config['url']+str(serial_no)+'.json'
    headers = {'content-type':'application/json'}
    data = {"time":time.time(),"coin":coin.total,"sending":0,"online":"1","wifi":wm.get_address(),"server":ip_address,"localtime":time.localtime()}
    response = urequests.put(url,json=data,headers=headers)
    response.close()

def updateOffline():
    headers = {'content-type':'application/json'}
    data = "0"
    url = config['url']+str(serial_no)+'/online.json'
    response = urequests.put(url,json=data,headers=headers)
    print("OFFLINE")
def round_to_nearst_10(x):
    if x % 10 == 0 :
        return x
    else :
        return math.ceil(x/10)*10
    
#pws = machine.PWM(machine.Pin(4),machine.Pin.OUT)

def sendPWM():
    global sss
    headers = {'content-type':'application/json'}
    url = config['url']+str(serial_no)+'/sending.json'
    response = urequests.get(url,headers=headers)
    res = int(response.json())
    response.close()
    sss = int(res)
    if res > 0 :
        for value in range(0,res) :
            pwm.value(1)
            time.sleep(0.03)
            pwm.value(0)
            time.sleep(0.03)
        data = "0"
        response = urequests.put(url,json=data,headers=headers)
        response.close()
        coin.total=res
        coin.bill_last_state = 0
        coin.checkandstart = 1
        coin.last_pulse_state = 1
        sss = 0
        print("OK")

curren  =  0
oldtotal  =  0
data = {"serial":serial_no,"coin":coin.total,"time":time.time()}
coin.checkandstart = 0
sss = 0
try :
  updateOnline()
  while True:
        led.value(0)
        time.sleep(config['autoload'])
        led.value(1)
        if oldtotal != coin.total and coin.bill_last_state == 0  and coin.last_pulse_state == 1  and coin.checkandstart == 1:
            coin.bill_pulse_count = coin.bill_pulse_count
            coin.total = coin.total*10
            oldtotal = coin.total
            data = {"serial":serial_no,"coin":coin.total,"time":time.time()}
            print("total:",coin.total,coin.bill_pulse_count)
            putdata(coin.total)
            coin.checkandstart = 0
        if oldtotal != coin.total and coin.bill_last_state == 0  and coin.last_pulse_state == 1 and coin.checkandstart == 0:
            print("And Check")
            coin.checkandstart = 1
        if sss == 0 :
            sendPWM()
        time.sleep(0.1)
finally:
    updateOffline()

