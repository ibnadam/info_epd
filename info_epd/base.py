import sys
import os
import logging
import time
import signal

from PIL import (
    Image,
    ImageDraw
)

from config import *


def custome_except_handler(exc_type, value, traceback):
    base = Base(err=True)
    base.show_err(exc_type, value, traceback)
sys.excepthook = custome_except_handler

        
class Base:
    """
    DST started on Sunday 08 March 2020, 02:00 local standard time (PST)
    DST ends on Sunday 01 November 2020, 02:00 local daylight time (PDT)
    """
    default_wait_time = 5

    def __init__(self, err=False):
        self.err = err
        self._done_setup = False
    
        self.epd = epd.EPD()
        self.epdconfig = epd.epdconfig
        self.clear()

        self.flip = False
        self._funcs = {}
        self._funcs['setup'] = []
        self._funcs['update'] = []
        self._funcs['redraw'] = []

    def setup(self):
        logging.info('Setup...')
        logging.info(self._funcs)
        
        self.update_info = {}
        self.update_info['next_secs'] = 86400 # 1 day

        def cleanup(*args):
            logging.warning("Received shutdown signal, cleanup...")
            if EPD_USED == EPD2in13:
                self.epd.init(self.epd.FULL_UPDATE)
                self.epd.Clear(0xFF)
            else:
                self.epd.init()
                self.epd.Clear()
            self.epdconfig.module_exit()
            sys.exit()

        signal.signal(signal.SIGINT, cleanup)
        signal.signal(signal.SIGTERM, cleanup)
        
        for f in self._funcs['setup']:
            f()

        self._done_setup = True
            
    def run(self, test=False, override_secs=0):
        logging.info('Run...')
        
        if not self._done_setup:
            self.setup()
            
        if test:
            self.test()
            return

        while True:
            self.update(override_secs)
    
    def update(self, override_secs=0):
        for f in self._funcs['update']:
            f()

        next_secs = override_secs if override_secs else self.update_info['next_secs']
        
        self.redraw()
        self.show()

        self.wait(next_secs)
    
    def redraw(self):
        if self.flip:
            hw = (self.epd.width, self.epd.height)
        else:
            hw = (self.epd.height, self.epd.width)
        self.image = Image.new('1', hw, 255) # 255: clear frame
        self.draw = ImageDraw.Draw(self.image)
        
        for f in self._funcs['redraw']:
            f()

    def show(self):
        if ROTATE180:
            self.image = self.image.rotate(180)
        self.epd.display(self.epd.getbuffer(self.image))
    
    def wait(self, wait_time=None):
        if not wait_time:
            wait_time = self.default_wait_time
        logging.info("Wait %d secs" % wait_time)
        time.sleep(wait_time)

    def clear(self):
        logging.info("Clear...")
        if EPD_USED == EPD2in13:
            self.epd.init(self.epd.FULL_UPDATE)
            self.epd.Clear(0xFF)
        else:
            self.epd.init()
            self.epd.Clear()

    def stop(self):
        logging.info("Sleep...")
        self.epd.sleep()

    def exit(self):
        logging.info("Exit...")
        self.epdconfig.module_exit()
        sys.exit()

    def test(self):
        # read bmp file 
        logging.info("Test: Read image file...")

        if self.flip:
            hw = (self.epd.width, self.epd.height)
        else:
            hw = (self.epd.height, self.epd.width)
        image1 = Image.new('1', hw, 255)  # 255: clear the frame
        bmp = Image.open(os.path.join(imgdir, 'masjid.bmp'))
        image1.paste(bmp, (2,2))    
        self.epd.display(self.epd.getbuffer(image1))
        
        time.sleep(10)

    def show_err(self, exc_type, value, traceback):
        if self.flip:
            hw = (self.epd.width, self.epd.height)
        else:
            hw = (self.epd.height, self.epd.width)
        image = Image.new('1', hw, 255) # 255: clear frame    
        draw = ImageDraw.Draw(image)
        draw.text((0, 10), "Error:", font=font18, fill=0)
        draw.text((0, 30), f'{value}', font=font18, fill=0)

        if ROTATE180:
            image = image.rotate(180)
        self.epd.display(self.epd.getbuffer(image))

        logging.error("Unhandled error", exc_info=(exc_type, value, traceback))
    
