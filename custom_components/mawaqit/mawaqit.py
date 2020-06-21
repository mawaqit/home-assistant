from datetime import datetime, timedelta
import json
import requests
import os


class PrayerTimesCalculator:



    
    def __init__(
        self,
        latitude: float,
        longitude: float,
        api_key: str,
        date: str,
    ):

        self._latitude = latitude
        self._longitude = longitude
        self._api_key = api_key

        date_parsed = datetime.strptime(date, "%Y-%m-%d")
        self._timestamp = int(date_parsed.timestamp())
    



    def fetch_prayer_times(self):
      api_token = self._api_key
      current_dir = os.path.dirname(os.path.realpath(__file__))
      text_file = open('{}/data/api.txt'.format(current_dir), "r")
      api_token = text_file.read()
      text_file.close()
      
      
      headers = {'Content-Type': 'application/json',
             'Api-Access-Token': format(api_token)}	
             
      
      current_dir = os.path.dirname(os.path.realpath(__file__))
      text_file = open('{}/data/mosquee.txt'.format(current_dir), "r")
      mosque_id = text_file.read()
      text_file.close()
      
      api_url_base = 'https://mawaqit.net/api/2.0/'
      api_url = api_url_base + 'mosque/' + mosque_id + '/prayer-times'
      """
      current_dir = os.path.dirname(os.path.realpath(__file__))
      text_file = open('{}/data/test.txt'.format(current_dir), "w")
      n = text_file.write(api_url)
      text_file.close()
"""
      response = requests.get(api_url, headers=headers)
      s1 = response.json()["times"][0]
      formater = '%H:%M'
      d = datetime.strptime(s1, formater) - timedelta(hours=0, minutes=10)

      if response.status_code == 200:
      	  
          myjson3 = {
                'Fajr': response.json()["times"][0],
                'Sunrise': response.json()["shuruq"],
                'Dhuhr': response.json()["times"][1],
                'Asr': response.json()["times"][2],
                'Sunset': response.json()["times"][3],
                'Maghrib': response.json()["times"][3],
                'Isha': response.json()["times"][4],
                'Imsak': d.strftime('%H:%M'),
                'Midnight': '00:00',
                'Jumua': response.json()["jumua"],
                'Shuruq': response.json()["shuruq"]
            }
          return myjson3 
      else:
          return response.status_code
          
          
          
         



