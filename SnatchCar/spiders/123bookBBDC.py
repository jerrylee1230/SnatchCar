# -*- coding: utf-8 -*-
from datetime import datetime
#import sys
import scrapy

import smtplib

from scrapy.mail import MailSender

import smtplib  

def send_notification(body):
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login("email.com", "password")
    #print(subject)
    print(body)
    server.sendmail("email@gmail.com", "email@gmail.com", body)
    server.quit()

#send_notification("testing")"""

########## Configuration begins here ##########

# Self explanatory. The username you use to log into bbdc.sg
username = 's9712989d'

# The password you use to log into bbdc.sg
pin = '210497'

# How many days ahead to book
daysCapWeekday = 12
daysCapWeekend = 24

# Which session numbers (1-8) to book
sessionsToBookWeekdays = ['2', '3', '4','5','6', '7','8']
sessionsToBookWeekends = []

"""
1(07:30 – 09:10)
2(09:20 – 11:00)
3(11:30 – 13:10)
4(13:20 – 15:00)
5(15:20 – 17:00)
6(17:10 – 18:50)
7(19:20 – 21:00)
8(21:10 – 22:50)
"""

# Which days to book.
# Note that day #1 is Sunday, #2 is Monday, ..., and #7 is Saturday
weekdays = ['2', '3', '4','5','6']
weekends = []

########### Configuration ends here ###########

# Note that this bookedSlots system is not ideal,
# the system won't rebook slots that it has tried
# to book but failed (e.g. someone else has got it
# but the same slot was cancelled again)
bookedSlots = []
checkWeekday = False

class Book(scrapy.Spider):
    name = "bookBBDC"
    start_urls = ['https://www.bbdc.sg/bbdc/bbdc_web/newheader.asp']
    custom_settings = {
        'DOWNLOADER_CLIENT_TLS_METHOD': 'TLSv1.0',
        'DUPEFILTER_DEBUG': True
    }

    
#    download_delay = 5

    def parse(self, response):
        return scrapy.FormRequest.from_response(
            response,
            formdata={
                'txtNRIC': username,
                'txtPassword': pin,
                'btnLogin': '+'},
            dont_filter=True,
            callback=self.afterLogin
        )

    def afterLogin(self, response):
        if "All sessions timeout after 20 minutes of inactivity." in response.body.decode("utf-8"):
            print("Timed out, logging in again.")
            return scrapy.Request('https://www.bbdc.sg/bbdc/bbdc_web/newheader.asp', dont_filter=True,
                                  callback=self.parse)
        # check login succeed before going on
        if "Please try again" in response.body.decode("utf-8"):
            print("Login failed: please check your username and password.")
            return
#        send_notification("hi")
        print("Login successful.")
        return scrapy.Request("https://www.bbdc.sg/bbdc/b-3c-pLessonBooking.asp?limit=pl", dont_filter=True,
                              callback=self.bookingPage)

    def bookingPage(self, response):
        if "All sessions timeout after 20 minutes of inactivity." in response.body.decode("utf-8"):
            print("Timed out, logging in again.")
            return scrapy.Request('https://www.bbdc.sg/bbdc/bbdc_web/newheader.asp', dont_filter=True,
                                  callback=self.parse)
        global checkWeekday
        checkWeekday = not checkWeekday
        print("Checking Weekdays: <{}>".format(weekdays) if checkWeekday else "Checking Weekends: <{}>".format(weekends))
        return scrapy.FormRequest.from_response(
            response,
            formname='frmSelectSchedule',
            formdata={
                'Month': ['Mar/2018', 'Apr/2018', 'May/2018'],  # TODO: autogen this
                'Session': sessionsToBookWeekdays if checkWeekday else sessionsToBookWeekends,
                'Day': weekdays if checkWeekday else weekends,
                'defPLVenue': '1',
                'optVenue': '1'},
            dont_filter=True,
            callback=self.availableSlots
        )

    def availableSlots(self, response):
        mailer = MailSender()
        #global send_notification
        def getDate(daySelector):
            return daySelector.css("td.txtbold::text").extract_first()

        def getSessions(daySelector):
            return daySelector.css("input[type='checkbox']::attr(value)").extract()

        #def getSessionNumber(daySelector):
        	#return int((daySelector.css("input[type='checkbox']::attr(id)").extract()).split("_")[1]) + 1

        if "All sessions timeout after 20 minutes of inactivity." in response.body.decode("utf-8"):
            print("Timed out, logging in again.")
            return scrapy.Request('https://www.bbdc.sg/bbdc/bbdc_web/newheader.asp', dont_filter=True,
                                  callback=self.parse)
        # check if there are any available slots
        filename = 'response.html'
        _f = 'booked.log'
        with open(filename, 'wb') as f:
            f.write(response.body)

        # lazy blacklist
        blacklist = [u'03/04/2018', u'04/04/2018']


        if "There is no more slots available. Please select another schedule" in response.body.decode("utf-8"):
            print("There are no slots at the moment that matches your criteria.")
            return scrapy.Request("https://www.bbdc.sg/bbdc/b-3c-pLessonBooking.asp?limit=pl", dont_filter=True,
                                  callback=self.bookingPage)
        # there are available slots here - now let's book it
        # iterate through each day
        days = response.css("tr[bgcolor='#FFFFFF']")  # this happens to be a unique identifier for each row aka day
        dates = map(getDate, days)
        sessions = map(getSessions, days)
        #session_numbers = map(getSessionNumber, days)

        bookingDates = []
        submitSlots = []
        bookingSessionNumbers = []
        for date, session, in zip(dates, sessions):
            date_format = "%d/%m/%Y"
            dateObj = datetime.strptime(date, date_format)
            delta = dateObj - datetime.today()
            global checkWeekday
            with open(_f, 'a') as f:
                f.write("{} in blacklist: {}\n".format(date, date in blacklist))
            if delta.days > daysCapWeekday and checkWeekday:
                continue
            elif delta.days > daysCapWeekend and not checkWeekday:
                continue
            elif session in bookedSlots:
                continue
            elif date in blacklist:
                continue
            bookingDates.extend(date)
            submitSlots.extend(session)  # i'm just going to ignore consecutive bookings
            bookedSlots.extend(session)
            #bookingSessionNumbers.extend(s_number)
        if len(submitSlots) == 0:
            print("There are no slots at the moment that matches your criteria.")
            return scrapy.Request("https://www.bbdc.sg/bbdc/b-3c-pLessonBooking.asp?limit=pl", dont_filter=True,
                                  callback=self.bookingPage)
       # print("Booking the following slot(s): ")
        mailer = MailSender(smtphost ="smtp.gmail.com", smtpport=587, smtpuser = "zhengyangchoong40@gmail.com", smtppass="adspwrsojpgxygag" )
       
       # send_notification(submitSlots[0])
        if len(bookingDates) == 1:
            message = str(bookingDates[0])
        else:
            message = str(bookingDates)
        mailer.send(to=["nicoleannlim1999@gmail.com"], subject="booking", body = "greetings nicole jiejie OwO we made a bookie wookie on {}!! \n This is a computer generated message. No signature is required.".format(message))
        #print(submitSlots)
        with open(_f, 'a+rw') as gf:
            gf.write('{} Trying to book: {} session {} \n \n'.format(datetime.now() , message, bookingSessionNumbers ))
        #send_notification()

        #return scrapy.Request("https://www.bbdc.sg/bbdc/b-3c-pLessonBooking.asp?limit=pl", dont_filter=True, callback=self.bookingPage)
        # not actually book anything 
        
        return scrapy.FormRequest.from_response(
            response,
            formname='myform',
            formdata={
                'slot': submitSlots
            },
            dont_filter=True,
            callback=self.bookingConfirm
        )

    def bookingConfirm(self, response):
        if "All sessions timeout after 20 minutes of inactivity." in response.body.decode("utf-8"):
            print("Timed out, logging in again.")
            return scrapy.Request('https://www.bbdc.sg/bbdc/bbdc_web/newheader.asp', dont_filter=True,
                                  callback=self.parse)
        return scrapy.FormRequest.from_response(
            response,
            callback=self.bookingConfirmed,
            dont_filter=True
        )

    def bookingConfirmed(self, response):
        if "All sessions timeout after 20 minutes of inactivity." in response.body.decode("utf-8"):
            print("Timed out, logging in again.")
            return scrapy.Request('https://www.bbdc.sg/bbdc/bbdc_web/newheader.asp', dont_filter=True,
                                  callback=self.parse)
        if "You have insufficient fund in your account. Please top up your account." in response.body.decode("utf-8"):
            print(
                "Looks like you have no more money in your account. Please put in some more money or I can't book anything.")
            return
        return scrapy.Request("https://www.bbdc.sg/bbdc/b-3c-pLessonBooking.asp?limit=pl", dont_filter=True,
                              callback=self.bookingPage)
