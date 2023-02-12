from machine import Pin, I2C
from time import sleep
from lcd1602 import LCD1602_RGB
import utime

WATERMARK_MAX = 110
WATERMARK_LOW = 40
WATERMARK_HIGH = 60

# The PIN layouts

''' Ranger pin number '''
rangerPinNumber = 16

''' Setting up the display. '''
i2c = I2C(1,scl=Pin(7), sda=Pin(6), freq=400000)
d = LCD1602_RGB(i2c, 2, 16)
d.set_rgb(0, 255, 0)

''' Setting up th button. '''
btnled = Pin(18, Pin.OUT)
button = Pin(19, Pin.IN, Pin.PULL_UP)# button connect to D18
button.irq(lambda pin: InterruptsButton(),Pin.IRQ_FALLING)#Set key interrupt

''' Setting up the relay. '''
relay = Pin(20, Pin.OUT)

class STATES():
    IDLE    = 1
    POMPING = 2
    ERROR   = 3
    MANUAL  = 4

def ultra():
    distance: int = 0
    
    the_pin = Pin(rangerPinNumber, Pin.OUT)
    the_pin.low()
    utime.sleep_us(2)
    the_pin.high()
    utime.sleep_us(5)
    the_pin.low()

    the_pin = Pin(rangerPinNumber, Pin.IN)

    while the_pin.value() == 0:
       signaloff = utime.ticks_us()
       
    while the_pin.value() == 1:
       signalon = utime.ticks_us()
       
    timepassed = signalon - signaloff
    distance = (timepassed * 0.0343) / 2
    print("The distance from object is ",distance,"cm")
    return distance

def r_set(val) -> None:
    btnled.value(val)
    relay.value(val)
    
def r_on():
    r_set(1)
    d.set_rgb(0, 255, 0)

def r_off():
    r_set(0)
    d.set_rgb(5, 5, 5)


'''Key interrupt function, change the state of the light when the key is pressed'''
def InterruptsButton():
    state.do_event("button")


class StateMachine:
    def __init__(self):
        self.myState = STATES.IDLE
        self.manualTimer: int = 0
        self.level: int = 0
        self.pomped: int = 0
        self.pompTime: int = 0
        
        d.clear()
        d.home()
        d.print('Starting Tom')
        r_on()
        sleep(2)
        d.clear()
        r_off()
        self.show_display()
        
    def show_display(self):
        d.clear()
        d.home()
        d.print(self.state_to_name() + ":" + str(self.level))
        d.setCursor(0,1)

        if self.pomped > 0:
            self.pomp_avr = round(self.pompTime / self.pomped, 1)
        else:
            self.pomp_avr = 0
        d.print(f"Pomped:{self.pomped} {self.pomp_avr}s")
        
    def set_level(self, new_level):
        self.level = new_level
        if (self.level < 0):
            self.level = 0

    def state_to_name(self) -> str:
        if self.myState == STATES.IDLE:
            return "idle"
        if self.myState == STATES.POMPING:
            return "pomping"
        if self.myState == STATES.ERROR:
            return "error"
        if self.myState == STATES.MANUAL:
            return "manual"
        return "unkown"
        
    def do_event(self, event):
        method = "do_" + self.state_to_name() + "_" + event
        getattr(self, method)()
        self.show_display()

    def do_idle_timer(self):
        if self.level > WATERMARK_HIGH:
            self.pomped += 1
            r_on()
            self.myState = STATES.POMPING            
    
    def do_idle_button(self):
        r_on()
        self.manualTimer = 5
        self.myState = STATES.MANUAL
        
    def do_pomping_timer(self):
        if self.level > WATERMARK_LOW:
            self.pompTime += 1
        else:
            r_off()
            self.myState = STATES.IDLE
            
    def do_pomping_button(self):
            r_off()
            self.manualTimer = 0
            self.myState = STATES.IDLE
    
    def do_manual_timer(self):
        if self.manualTimer > 0:
            self.manualTimer -= 1
        else:
            r_off()
            self.manualTimer = 0
            self.myState = STATES.IDLE
            
    def do_manual_button(self):
        r_off()
        self.manualTimer = 0
        self.myState = STATES.IDLE

state = StateMachine()

while True:
    sleep(1)
    dist = ultra()
    level = WATERMARK_MAX - dist
    state.set_level(level)
    state.do_event("timer")


