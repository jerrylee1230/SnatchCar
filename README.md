# SnatchCar
This is an application that automatically looks for and books cancelled driving slots on Bukit Batok Driving Centre's online booking portal. It works by continuously querying the portal for available slots and checking if any slots meet the user defined criteria, and books those slots.

The meat of the application is contained within the bookBBDC spider and the spider can be run after entering your credentials and booking criteria.

The application is built upon the Scrapy library, and generally it is a good idea to run the application on ScrapingHub, a cloud service that runs Scrapy spiders (1 spider can be run at a time free of charge).

No payment was received for the glowing review of ScrapingHub.

Unfortunately, SnatchCar does not yet work for SSDC, which uses Javascript alert boxes and popups. 