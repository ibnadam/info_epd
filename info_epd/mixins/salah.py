import sys
import os
import logging
import time
import datetime

from PIL import (
    Image,
    ImageDraw,
    ImageFont
)

from config import *
from util import *

from info_epd import praytimes


DEBUG_PRAYTIMES = False


class SalahMixin:
    """Uses praytimes library for calculating prayer times.

    Make sure settings are correct for your location, Madhab, etc.
    Especially check:
    * Caluclation methos
    * Settings for Maghrib & midnight
    """
    calc_method = 'ISNA'
    time_fmt = '12h'
    
    def __init__(self):
        self._funcs['setup'].append(self.setup_praytimes)
        self._funcs['update'].append(self.update_praytimes)
        self._funcs['redraw'].append(self.redraw_praytimes)

    def setup_praytimes(self):
        logging.info("Setup praytimes...")
        
        self.pt = praytimes.PrayTimes()
        
        self.pt.setMethod(self.calc_method)

        params = dict(
            fajr=15,
            maghrib='0 min',
            isha=15,
            midnight='Jafari' #doublecheck: seems to be more correct than non-jafari
        )
        self.pt.adjust(params)

        self.update_info['praytimes'] = {}
        self.update_info['praytimes']['pt'] = None
        self.update_info['praytimes']['curr'] = None
        self.update_info['praytimes']['curr_end'] = None
        self.update_info['praytimes']['next_time'] = None
        

    def update_praytimes(self):
        logging.info("Update praytimes...")

        today = get_today()
        tomorrow = get_tomorrow()
        now = get_now()

        coords = COORDS['Culver City']
        timezone = TIMEZONES['Los Angeles']
        dst = time.localtime().tm_isdst
        pt = self.pt.getTimes(today, coords,
                              timezone, dst, self.time_fmt)

        fmt = '%I:%M%p'
        def to_time_obj(p1):
            p2 = datetime.datetime.strptime(pt[p1], fmt)
            def to_date_obj():
                return datetime.datetime(year=now.year, month=now.month, day=now.day,
                                         hour=p2.hour, minute=p2.minute)
            return to_date_obj
            
        fajr = to_time_obj('fajr')()
        sunrise = to_time_obj('sunrise')()
        dhuhr = to_time_obj('dhuhr')()
        asr = to_time_obj('asr')()
        maghrib = to_time_obj('maghrib')()
        isha = to_time_obj('isha')()
        midnight = to_time_obj('midnight')()

        # Assume maghrib lasts for 45 mins
        maghrib_end = maghrib + datetime.timedelta(minutes=45)

        # Figure out what applies to current time
        curr = {}
        curr['fajr'] = fajr <= now < sunrise
        after_fajr = sunrise <= now < dhuhr
        curr['dhuhr'] = dhuhr <= now < asr
        curr['asr'] = asr <= now < maghrib
        curr['maghrib'] = maghrib <= now < maghrib_end
        after_maghrib = maghrib_end <= now < isha

        # Check isha time (could be past 00:00)
        is_isha = False
        if not any((curr['fajr'], curr['dhuhr'], curr['asr'], curr['maghrib'],
                    after_fajr, after_maghrib)):
            # Either we are before fajr, or after isha
            after_isha = now >= isha
            if after_isha:
                m_hr = midnight.hour
                if m_hr < fajr.hour:
                    m_hr += 24
                m_min = midnight.minute
                n_hr = now.hour
                n_min = now.minute
                if n_hr < m_hr:
                    is_isha = True
                elif n_hr == m_hr:
                    if n_min < m_min:
                        is_isha = True
        curr['isha'] = is_isha

        # Figure out what comes next
        next_secs, next_time = secs_til_midnight(), 'midnight'
        next_prayer, pt['next_fajr'] = 'next_fajr', None
        curr_end = None
        if curr['fajr']:
            next_secs, next_time = (sunrise - now).seconds, pt['sunrise']
            curr_end = pt['sunrise']
            next_prayer = 'dhuhr'
        elif after_fajr:
            next_secs, next_time = (dhuhr - now).seconds, pt['dhuhr']
            next_prayer = 'dhuhr'
        elif curr['dhuhr']:
            next_secs, next_time = (asr - now).seconds, pt['asr']
            curr_end = pt['asr']
            next_prayer = 'asr'
        elif curr['asr']:
            next_secs, next_time = (maghrib - now).seconds, pt['maghrib']
            curr_end = pt['maghrib']
            next_prayer = 'maghrib'
        elif curr['maghrib']:
            maghrib_end_t = maghrib_end.strftime('%I:%M%p')
            next_secs, next_time = (maghrib_end - now).seconds, maghrib_end_t
            curr_end = maghrib_end_t
            next_prayer = 'isha'
        elif after_maghrib:
            next_secs, next_time = (isha - now).seconds, pt['isha']
            next_prayer = 'isha'
        elif curr['isha']:
            curr_end = pt['midnight']
        elif now < fajr:
            next_secs, next_time = (fajr - now).seconds, pt['fajr']
            next_prayer = 'fajr'

        # Need to get next day's times
        if next_prayer == 'next_fajr':
            next_pt = self.pt.getTimes(tomorrow, coords,
                                       timezone, dst, self.time_fmt)
            pt['next_fajr'] = next_pt['fajr']
            
        # Save info
        self.update_info['next_secs'] = next_secs
        self.update_info['praytimes']['pt'] = pt
        self.update_info['praytimes']['curr'] = curr
        self.update_info['praytimes']['curr_end'] = curr_end
        self.update_info['praytimes']['next_time'] = next_time
        self.update_info['praytimes']['next_prayer'] = next_prayer

    def redraw_praytimes(self):
        logging.info("Redraw praytimes...")

        if EPD_USED == EPD2in13:
            self.redraw_praytimes_partial()
        else:
            self.redraw_praytimes_full()
            
    def redraw_praytimes_partial(self):
        pinfo = self.update_info['praytimes']
        pt, curr, curr_end = pinfo['pt'], pinfo['curr'], pinfo['curr_end']
        next_upd, next_prayer = pinfo['next_time'], pinfo['next_prayer']

        h, w = self.epd.height, self.epd.width

        bmp = Image.open(os.path.join(imgdir, 'masjid.bmp'))
        self.image.paste(bmp, (2,w//2+25))    

        # If have current end time then we have a current prayer time as well
        font = font24
        if curr_end:
            for p in curr:
                if curr[p]:
                    txt = f"{p.capitalize()}: {pt[p]}"
                    x, y = font.getsize(txt)
                    self.draw.rectangle([(5,5),(x+15,y+15)], fill='black')
                    self.draw.text((10,10), txt, font=font, fill='white')
                    self.draw.text((10, y+15), f'Ends {curr_end}', font=font18, fill=0)
        else:
            txt = f'Next update: {next_upd}'
            self.draw.text((10, 10), txt, font=font, fill=0)
            
        # Next prayer
        self.draw.text((55,w//2+10), 'Upcoming:', font=font18, fill=0)
        p = next_prayer
        n = 'fajr' if p=='next_fajr' else p
        txt = f"{n.capitalize()}: {pt[p]}"
        self.draw.text((55,w//2+30), txt, font=font, fill=0)
            
        
    def redraw_praytimes_full(self):
        """To be implemented"""
