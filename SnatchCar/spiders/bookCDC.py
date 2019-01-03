#
# This is a WIP and is not functional for any practical purposes at the moment. Do not use.
#

import scrapy
import time
from datetime import datetime

########## Configuration begins here ##########

#Self explanatory. The username you use to log into bbdc.sg
username = 'REDACTED'

#The password you use to log into bbdc.sg
pin = 'SUPER REDACTED'

#How many days ahead to book
#daysCap = 24

#Which session numbers (1-8) to book
sessionsToBookWeekdays = ['6','7','8']
sessionsToBookWeekends = ['2','3','4','5','6','7','8']

#Which days to book. 
#Note that day #1 is Sunday, #2 is Monday, ..., and #7 is Saturday
weekdays = ['2','3','4','5','6']
weekends = ['1','7']

########### Configuration ends here ###########

bookedSlots = []
checkWeekday = False

class Book(scrapy.Spider):
    name = "bookCDC"
    start_urls = ['https://www.cdc.com.sg/']
    custom_settings = {
        #'DOWNLOADER_CLIENT_TLS_METHOD': 'TLSv1.0',
        'DUPEFILTER_DEBUG': True
    }

    def parse(self, response):
        return [scrapy.FormRequest(url="https://www.cdc.com.sg/NewPortal/",
                    formdata={'LearnerID': username, 'Pswd': pin},
                    callback=self.afterLogin)]

    def afterLogin(self, response):
        #if "All sessions timeout after 20 minutes of inactivity." in response.body.decode("utf-8"):
        #    print("Timed out, logging in again.")
        #    return scrapy.Request('https://www.bbdc.sg/bbdc/bbdc_web/newheader.asp', dont_filter = True, callback=self.parse)
        # check login succeed before going on
        #if "Please try again" in response.body.decode("utf-8"):
        #    print("Login failed: please check your username and password.")
        #    return
        #print("Login successful.")
        return scrapy.Request("https://www.cdc.com.sg/NewPortal/Booking/BookingPL.aspx", dont_filter = True, callback=self.bookingPage)
    
    def bookingPage(self, response):
        #if "All sessions timeout after 20 minutes of inactivity." in response.body.decode("utf-8"):
        #    print("Timed out, logging in again.")
        #    return scrapy.Request('https://www.bbdc.sg/bbdc/bbdc_web/newheader.asp', dont_filter = True, callback=self.parse)
        #global checkWeekday
        #checkWeekday = not checkWeekday
        #return scrapy.FormRequest.from_response(
        #    response,
        #    formname='frmSelectSchedule',
        #    formdata={
        #        'Month': ['Jan/2017','Feb/2017'], #TODO: autogen this
        #        'Session': sessionsToBookWeekdays if checkWeekday else sessionsToBookWeekends,
        #        'Day': weekdays if checkWeekday else weekends,
        #        'defPLVenue': '1',
        #        'optVenue': '1'},
        #    dont_filter = True,
        #    callback=self.availableSlots
        #)
        filename = 'response.html'
        with open(filename, 'wb') as f:
            f.write(response.body)
    
    def availableSlots(self, response):
        def getDate(daySelector):
            return daySelector.css("td.txtbold::text").extract_first()
        def getSessions(daySelector):
            return daySelector.css("input[type='checkbox']::attr(value)").extract()
        if "All sessions timeout after 20 minutes of inactivity." in response.body.decode("utf-8"):
            print("Timed out, logging in again.")
            return scrapy.Request('https://www.bbdc.sg/bbdc/bbdc_web/newheader.asp', dont_filter = True, callback=self.parse)
        #check if there are any available slots
        filename = 'response.html'
        with open(filename, 'wb') as f:
            f.write(response.body)
        if "There is no more slots available. Please select another schedule" in response.body.decode("utf-8"):
            print("There are no slots at the moment that matches your criteria.")
            return scrapy.Request("https://www.bbdc.sg/bbdc/b-3c-pLessonBooking.asp?limit=pl", dont_filter = True, callback=self.bookingPage)
        #there are available slots here - now let's book it
        #iterate through each day
        days = response.css("tr[bgcolor='#FFFFFF']") #this happens to be a unique identifier for each row aka day
        dates = map(getDate, days)
        sessions = map(getSessions, days)
        submitSlots = []
        for date, session in zip(dates, sessions):
            date_format = "%d/%m/%Y"
            dateObj = datetime.strptime(date, date_format)
            #delta = dateObj - datetime.today()
            submitSlots.extend(session) #i'm just going to ignore consecutive bookings
        if len(submitSlots) == 0:
            print("There are no slots at the moment that matches your criteria.")
            return scrapy.Request("https://www.bbdc.sg/bbdc/b-3c-pLessonBooking.asp?limit=pl", dont_filter = True, callback=self.bookingPage)
        print("Booking the following slot(s): ")
        print(submitSlots)
        return scrapy.FormRequest.from_response(
            response,
            formname='myform',
            formdata={
                'slot': submitSlots
                },
            dont_filter = True,
            callback=self.bookingConfirm
        )

    def bookingConfirm(self, response):
        if "All sessions timeout after 20 minutes of inactivity." in response.body.decode("utf-8"):
            print("Timed out, logging in again.")
            return scrapy.Request('https://www.bbdc.sg/bbdc/bbdc_web/newheader.asp', dont_filter = True, callback=self.parse)
        return scrapy.FormRequest.from_response(
            response,
            callback=self.bookingConfirmed,
            dont_filter = True
        )
    
    def bookingConfirmed(self, response):
        if "All sessions timeout after 20 minutes of inactivity." in response.body.decode("utf-8"):
            print("Timed out, logging in again.")
            return scrapy.Request('https://www.bbdc.sg/bbdc/bbdc_web/newheader.asp', dont_filter = True, callback=self.parse)
        if "You have insufficient fund in your account. Please top up your account." in response.body.decode("utf-8"):
            print("Looks like you have no more money in your account. Please put in some more money or I can't book anything.")
            return
        return scrapy.Request("https://www.bbdc.sg/bbdc/b-3c-pLessonBooking.asp?limit=pl", dont_filter = True, callback=self.bookingPage)
