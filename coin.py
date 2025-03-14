import json

def writeFile(coin) :
    f = open('coin_data.json' , 'w') 
    f.write(coin) 
    f.close()


def readCoin() :
    f = open('coin_data.json') 
    data = f.read()
    f.close()
    coin = json.loads(data)
    return coin['coin']

bill_pulse_count = 0 
bill_last_state = 0 
total = 0
last_pulse_state = 0
checkandstart = 0
def coin_callback(p):
        global bill_pulse_count, bill_last_state, total , last_pulse_state,checkandstart
        pulse_state = p.value()
        bill_last_state = 0
        last_pulse_state = pulse_state
        bill_pulse_count = bill_pulse_count +1  #// increment the pulse counter
        total = bill_pulse_count * 1
        data = {"coin":total}
        json_data = json.dumps(data)
        print('last_state',pulse_state, "total money", total)
        writeFile(json_data.encode())
        checkandstart = 0
