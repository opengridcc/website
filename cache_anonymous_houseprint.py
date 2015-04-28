# -*- coding: utf-8 -*-
"""
Script to cache anonymous houseprint data into hp_anonymous.pkl

Created on 05/07/2014 by Roel De Coninck
"""

import os, sys
import inspect
import config

c = config.Config()

sys.path.append(c.get('backend','opengrid'))
from library import houseprint

def cache():

	hp = houseprint.Houseprint()
	all_sensordata = hp.get_all_fluksosensors()
	print('Sensor data fetched')

	hp.save('hp_anonymous.pkl')