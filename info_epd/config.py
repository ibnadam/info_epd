import os
import logging

from PIL import ImageFont

from info_epd.waveshare_epd import epd2in13_V2
from info_epd.waveshare_epd import epd7in5_HD


# You must select your e-Ink display here
EPD2in13, EPD7in5 = range(2)
EPD_USED = EPD2in13

if EPD_USED == EPD2in13:
    epd = epd2in13_V2
else:
    epd = epd7in5_HD
    
# If you want image rotated 180 then set to True
ROTATE180 = True

#logging.basicConfig(level=logging.DEBUG)
logging.basicConfig(level=logging.WARNING)

currdir = os.path.dirname(os.path.realpath(__file__))
imgdir = os.path.join(currdir, 'images')
fontpath = os.path.join(imgdir, 'Font.ttc')
font5 = ImageFont.truetype(fontpath, 5)
font10 = ImageFont.truetype(fontpath, 10)
font15 = ImageFont.truetype(fontpath, 15)
font18 = ImageFont.truetype(fontpath, 18)
font24 = ImageFont.truetype(fontpath, 24)
font36 = ImageFont.truetype(fontpath, 36)
font36 = ImageFont.truetype(fontpath, 36)
font48 = ImageFont.truetype(fontpath, 48)
font64 = ImageFont.truetype(fontpath, 64)

TIMEZONES, COORDS = {}, {}
TIMEZONES['Los Angeles'] = -8
COORDS['Culver City'] = (34.009827, -118.411066)
