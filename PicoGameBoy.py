# Original source files for PicoGameBoy.py by Vincent Mistler for YouMakeTech
# Modified By HalloSpaceBoy for the PicoBoy
from machine import Pin, PWM, ADC
from framebuf import FrameBuffer, RGB565
from time import sleep
from random import randint
import struct
import sys
RAMWR     = b'\x2C'
from micropython import const
from machine import Pin, PWM, SPI
import framebuf
from time import sleep
from gc import collect

# register definitions
SWRESET   = b'\x01'
TEOFF     = b'\x34'
TEON      = b'\x35'
MADCTL    = b'\x36'
COLMOD    = b'\x3A'
GCTRL     = b'\xB7'
VCOMS     = b'\xBB'
LCMCTRL   = b'\xC0'
VDVVRHEN  = b'\xC2'
VRHS      = b'\xC3'
VDVS      = b'\xC4'
FRCTRL2   = b'\xC6'
PWCTRL1   = b'\xD0'
PORCTRL   = b'\xB2'
GMCTRP1   = b'\xE0'
GMCTRN1   = b'\xE1'
INVOFF    = b'\x20'
SLPOUT    = b'\x11'
DISPON    = b'\x29'
GAMSET    = b'\x26'
DISPOFF   = b'\x28'
RAMWR     = b'\x2C'
INVON     = b'\x21'
CASET     = b'\x2A'
RASET     = b'\x2B'
PWMFRSEL  = b'\xCC'

# Subclassing FrameBuffer provides support for graphics primitives
# http://docs.micropython.org/en/latest/pyboard/library/framebuf.html
class ST7789(framebuf.FrameBuffer):
    def __init__(self, width=240, height=240, id_=1, sck=10, mosi=11,
                 dc=8, rst=12, cs=9, bl=13, baudrate=62500000):
        self.width = width
        self.height = height
        self.spi = SPI(id_, sck=Pin(sck), mosi=Pin(mosi), baudrate=baudrate, polarity=0, phase=0)
        self.dc = Pin(dc, Pin.OUT)
        self.rst = Pin(rst, Pin.OUT)
        self.cs = Pin(cs, Pin.OUT)
        self.bl = Pin(bl, Pin.OUT)

        self.buffer = memoryview(bytearray(self.height * self.width * 2))
        super().__init__(self.buffer,self.width, self.height, framebuf.RGB565)
        
        self.init_display()
        
    def write_cmd(self, cmd=None, data=None):
        self.cs(0)
        if cmd:
            self.dc(0) # command mode
            self.spi.write(cmd)
        if data:
            self.dc(1) # data mode
            self.spi.write(data)
        self.cs(1)

    def init_display(self):
        
        # Hardware reset
        self.rst.value(1)
        sleep(0.150)
        self.rst.value(0)
        sleep(0.150)
        self.rst.value(1)
        sleep(0.150)
        
        self.bl.value(0) # Turn backlight off initially to avoid nasty surprises

        self.write_cmd(SWRESET)
        sleep(0.150)
        self.write_cmd(TEON) # enable frame sync signal if used
        self.write_cmd(COLMOD, b'\x05') # 16 bits per pixel
        self.write_cmd(PORCTRL, b'\x0c\x0c\x00\x33\x33')
        self.write_cmd(GCTRL, b'\x14')
        self.write_cmd(VCOMS, b'\x37')
        self.write_cmd(LCMCTRL, b'\x2c')
        self.write_cmd(VDVVRHEN, b'\x01')
        self.write_cmd(VRHS, b'\x12')
        self.write_cmd(VDVS, b'\x20')
        self.write_cmd(PWCTRL1, b'\xa4\xa1')
        self.write_cmd(FRCTRL2, b'\x0f')
        self.write_cmd(GMCTRP1, b'\xD0\x04\x0D\x11\x13\x2B\x3F\x54\x4C\x18\x0D\x0B\x1F\x23')
        self.write_cmd(GMCTRN1, b'\xD0\x04\x0C\x11\x13\x2C\x3F\x44\x51\x2F\x1F\x1F\x20\x23')
        
        self.write_cmd(INVON)   # set inversion mode
        self.write_cmd(SLPOUT)  # leave sleep mode
        self.write_cmd(DISPON)  # turn display on
        
        sleep(0.1)
        
        #self.write_cmd(CASET, b'\x00\x00\x00\xF0') #90 Degrees rotation
        #self.write_cmd(RASET, b'\x00\x00\x00\xF0')
        #self.write_cmd(MADCTL, b'\x04')
        self.write_cmd(CASET, b'\x00\x00\x00\xEF') #-> (F0 to EF)
        self.write_cmd(RASET, b'\x00\x00\x00\xEF') #-> (F0 to EF)
        self.write_cmd(MADCTL, b'\x70') #-> (04 to 70)

        self.fill(0)
        self.show()
        sleep(0.050)
        self.bl.value(1)

    def power_off(self):
        pass

    def power_on(self):
        pass

    def contrast(self, contrast):
        pass

    def invert(self, invert):
        pass

    def rotate(self, rotate):
        pass

    def show(self):
        self.write_cmd(RAMWR, self.buffer)
    
    def color(r, g, b):
        """
        color(r, g, b) returns a 16 bits integer color code for the ST7789 display


        where:
            r (int): Red value between 0 and 255
            g (int): Green value between 0 and 255
            b (int): Blue value between 0 and 255
        """
        # rgb (24 bits) -> rgb565 conversion (16 bits)
        # rgb = r(8 bits) + g(8 bits) + b(8 bits) = 24 bits
        # rgb565 = r(5 bits) + g(6 bits) + b(5 bits) = 16 bits
        r5 = (r & 0b11111000) >> 3
        g6 = (g & 0b11111100) >> 2
        b5 = (b & 0b11111000) >> 3
        rgb565 = (r5 << 11) | (g6 << 5) | b5
        
        # swap LSB and MSB bytes before sending to the screen
        lsb = (rgb565 & 0b0000000011111111)
        msb = (rgb565 & 0b1111111100000000) >> 8
        
        return ((lsb << 8) | msb)
    
    def load_image(self,filename):
        open(filename, "rb").readinto(self.buffer)
        
    def get_pixel(self, x, y):
        byte1=self.buffer[2*(y*self.width+x)];
        byte2=self.buffer[2*(y*self.width+x)+1];
        return byte2*256+byte1
collect()
class PicoGameBoy(ST7789):
    def __init__(self):
        self.__up = Pin(2, Pin.IN, Pin.PULL_UP)
        self.__down = Pin(18, Pin.IN, Pin.PULL_UP)
        self.__left = Pin(16, Pin.IN, Pin.PULL_UP)
        self.__right = Pin(20, Pin.IN, Pin.PULL_UP)
        self.__button_A = Pin(15, Pin.IN, Pin.PULL_UP)
        self.__button_B = Pin(17, Pin.IN, Pin.PULL_UP)
        self.__button_home = Pin(3, Pin.IN, Pin.PULL_UP)
        self.__button_select = Pin(19, Pin.IN, Pin.PULL_UP)
        self.__button_start = Pin(21, Pin.IN, Pin.PULL_UP)
        self.__buzzer = PWM(Pin(0))
        self.__buzzer2 = PWM(Pin(1))
        self.__buzzer3 = PWM(Pin(4))
        self.__buzzer4 = PWM(Pin(5))
        super().__init__(width=240, height=240, id_=1, sck=10, mosi=11,
                         dc=8, rst=12, cs=9, bl=13, baudrate=62500000)
        
        self.__fb=[] # Array of FrameBuffer objects for sprites
        self.__w=[]
        self.__h=[]
        self.vpin=ADC(29)
        self.audio_pwm_wrap=5000
        self.curve=1.8
        self.vol_max=100000#30000
        self.vol_min=2500
        try:
            with open("/volume.conf", "r") as r:
                self.vol=int(r.read())
        except:
            self.vol=self.vol_max
    # center_text(s,color) displays a text in the middle of 
    # the screen with the specified color
    def free_mem(self):
        import gc, sys
        for key in sys.modules:
            del sys.modules[key]
        gc.collect()
    
    def show(self):
        self.show_screen()
        if self.button_up() and self.button_select():
            self.increase_brightness()
        if self.button_down() and self.button_select():
            self.decrease_brightness()
        if self.button_right() and self.button_select():
            self.increase_vol()
        if self.button_left() and self.button_select():
            self.decrease_vol()
        
    def show_screen(self):
        self.write_cmd(RAMWR, self.buffer)
    def center_text(self, s, color = 1):
        x = int(self.width/2)- int(len(s)/2 * 8)
        y = int(self.height/2) - 8
        self.text(s, x, y, color)
        
    def create_text(self, s,x=-1,y=-1, color = ST7789.color(255,255,255)):
        if x==-1:
            x = int(self.width/2)- int(len(s)/2 * 8)
        if y==-1:
            y = int(self.height/2) - 8
        self.text(s, x, y, color)
        

    
    # center_text(s,color) displays a text in the right corner of 
    # the screen with the specified color
    def top_right_corner_text(self, s, color = 1):
        x = self.width - int(len(s) * 8)
        y = 0
        self.text(s, x, y, color)
        
        
    # add_sprite(buffer,w,h) creates a new sprite from framebuffer
    # with a width of w and a height of h
    # The first sprite is #0 and can be displayed by sprite(0,x,y)
    def add_sprite(self, buffer, w, h, r=1):
        if r==1:
            rotated_fb = FrameBuffer(buffer, w, h, RGB565)
        elif r==2:
            fb = FrameBuffer(buffer, w, h, RGB565)
            rotated_fb = FrameBuffer(bytearray(w*h*2), w, h, RGB565)
            for x in range(w):
                for y in range(h):
                    p=fb.pixel(x,y)
                    rotated_fb.pixel(-y+h,-x+w,p)
        elif r==3:
            fb = FrameBuffer(buffer, w, h, RGB565)
            rotated_fb = FrameBuffer(bytearray(w*h*2), w, h, RGB565)
            for x in range(w):
                for y in range(h):
                    p=fb.pixel(x,y)
                    rotated_fb.pixel(-x+w,-y+h,p)
        else:
            fb = FrameBuffer(buffer, w, h, RGB565)
            rotated_fb = FrameBuffer(bytearray(w*h*2), w, h, RGB565)
            for x in range(w):
                for y in range(h):
                    p=fb.pixel(x,y)
                    rotated_fb.pixel(y,x,p)
        self.__fb.append(rotated_fb)
        self.__w.append(w)
        self.__h.append(h)
        
        
    def replace_sprite_colors(self,sprite,color1,color2):
        width=self.__w[sprite]
        height=self.__h[sprite]
        for x in range(width):
            for y in range(height):
                if self.__fb[sprite].pixel(x,y)==color1:
                    self.__fb[sprite].pixel(x,y,color2)
                else:
                    self.__fb[sprite].pixel(x,y,self.__fb[sprite].pixel(x,y))
                
        
    # add_rect_sprite(color,w,h) creates a new rectangular sprite
    # with the specified color, width and height
    def add_rect_sprite(self, color, w, h):
        buffer = bytearray(w * h * 2) # 2 bytes per pixel
        # fill the buffer with the specified color
        lsb = (color & 0b0000000011111111)
        msb = (color & 0b1111111100000000) >> 8
        for i in range(0,w*h*2,2):
            buffer[i] = lsb
            buffer[i+1] = msb
        fb = FrameBuffer(buffer, w, h, RGB565)
        self.__fb.append(fb)
        self.__w.append(w)
        self.__h.append(h)
       
    # sprite(n,x,y) displays the nth sprite at coordinates (x,y)
    # the sprite must be created first by method add_sprite
    def sprite(self, n, x, y):
        self.blit(self.__fb[n], x, y)
        
    def load_binary_image(self, path, x, y,w,h):
        chunk_size = 16384
        start_index=20
        with open(path, 'rb') as file:
            while True:
                chunk = file.read(chunk_size)
                if not chunk:
                    break  
                for i, byte in enumerate(chunk):
                    self.buffer[start_index + i] = byte

        
    # sprite_width(n) returns the width of the nth sprite in pixels
    def sprite_width(self,n):
        return self.__w[n]
    
    # sprite_height(n) returns the height of the nth sprite in pixels
    def sprite_height(self,n):
        return self.__h[n]
        
    # button_up() returns True when the player presses the up button
    def button_up(self):
        return self.__up.value()==0
    
    # button_down() returns True when the player presses the down button
    def button_down(self):
        return self.__down.value()==0
    
    # button_left() returns True when the player presses the left button
    def button_left(self):
        return self.__left.value()==0
    
    # button_right() returns True when the player presses the right button
    def button_right(self):
        return self.__right.value()==0
    
    # button_A() returns True when the player presses the A button
    def button_A(self):
        return self.__button_A.value()==0
    
    # button_B() returns True when the player presses the B button
    def button_B(self):
        return self.__button_B.value()==0

    # button_Home() returns True when the player presses the home button
    def button_Home(self):
        return self.__button_home.value()==0

    # button_Home() returns True when the player presses the home button
    def button_start(self):
        return self.__button_start.value()==0

    # button_Home() returns True when the player presses the home button
    def button_select(self):
        return self.__button_select.value()==0

    # any_button() returns True if any button is pressed
    def any_button(self):
        button_pressed=False
        if self.button_up():
            button_pressed = True
        if self.button_down():
            button_pressed = True
        if self.button_left():
            button_pressed = True
        if self.button_right():
            button_pressed = True
        if self.button_A():
            button_pressed = True
        if self.button_B():
            button_pressed = True
        if self.button_select():
            button_pressed = True
        if self.button_start():
            button_pressed = True
        return button_pressed
    
    
        
    # sound(freq) makes a sound at the selected frequency in Hz
    # call sound(0) to stop playing the sound
    def increase_vol(self):
        if self.vol<=self.vol_max-5500:
            self.vol+=4875
        else:
            self.vol=self.vol_max
        try:
            with open("volume.conf", "w") as w:
                w.write(str(self.vol))
        except:
            ""
                
    def decrease_vol(self):
        if self.vol>=self.vol_min+5500:
            self.vol-=4875
        else:
            self.vol=self.vol_min
        try:
            with open("volume.conf", "w") as w:
                w.write(str(self.vol))
        except:
            ""
    
    def sound(self, freq, channel=1, j=0):
        pwm_divider = 133000000 / self.audio_pwm_wrap / (freq+1)
        max_count = (freq * self.audio_pwm_wrap) / 10000
        level = (self.vol / 100.0**self.curve) * max_count
        if channel==1:
            if freq>0:
                self.__buzzer.freq(freq)
                self.__buzzer.duty_u16(int(level))
            else:
                self.__buzzer.duty_u16(0)
        if channel==2:
            if freq>0:
                self.__buzzer2.freq(freq)
                self.__buzzer2.duty_u16(int(level))
            else:
                self.__buzzer2.duty_u16(0)
        if channel==3:
            if freq>0:
                self.__buzzer3.freq(freq)
                self.__buzzer3.duty_u16(int(level))
            else:
                self.__buzzer3.duty_u16(0)
        if channel==4:
            if freq>0:
                self.__buzzer4.freq(freq)
                self.__buzzer4.duty_u16(int(level))
            else:
                self.__buzzer4.duty_u16(0)
            
