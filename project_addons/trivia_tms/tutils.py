import pytz
from datetime import date, timedelta, datetime
from requests import get, post, HTTPError, utils
import json
from json import dumps
import http.client
import urllib.parse
import base64
import hmac
import hashlib
import random
import time
import os


class Tutils:

    def convert_float_time_to_second(float_time):
        hours = int(float_time) 
        minutes_decimal = float_time - hours
        minutes = int(minutes_decimal * 60)
        total_seconds = (hours * 3600) + (minutes * 60)
        return total_seconds

    def convert_local_datetime_to_utc_date_time(local_datetime, tz):
        local_timezone = pytz.timezone(tz)
        l_dtime = local_timezone.localize(local_datetime)
        utc_dtime = l_dtime.astimezone(pytz.utc)
        utc_naive_dtime = utc_dtime.replace(tzinfo=None)
        return utc_naive_dtime
    
    def daterange(start_date, end_date):
        for n in range(int((end_date - start_date).days)):
            yield start_date + timedelta(n)
    
    def getHereAuthToken():
        access_key = os.environ['HERE_ACCESS_KEY_ID']
        access_secret = os.environ['HERE_ACCESS_KEY_SECRET']

        url = "https://account.api.here.com/oauth2/token"  

        # Génération d'une chaîne aléatoire pour oauth_nonce
        oauth_nonce = ''.join([random.choice('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789') for i in range(32)])

        # Calcul du timestamp
        oauth_timestamp = str(int(time.time()))

        # Création des paramètres OAuth
        oauth_params = {
            "grant_type": "client_credentials",
            "oauth_consumer_key": access_key,
            "oauth_nonce": oauth_nonce,
            "oauth_signature_method": "HMAC-SHA256",
            "oauth_timestamp": oauth_timestamp,
            "oauth_version": "1.0"
        }
        

        # Tri des paramètres OAuth par clé
        sorted_params = sorted(oauth_params.items(), key=lambda x: x[0])

        # Création de la chaîne de paramètres encodée pour la signature
        param_string = "&".join([f"{param}={urllib.parse.quote(value, safe='')}" for param, value in sorted_params])
        base_string = f"POST&{urllib.parse.quote(url, safe='')}&{urllib.parse.quote(param_string, safe='')}"
        key = f"{urllib.parse.quote(access_secret, safe='')}&"

        # Création de la signature OAuth
        signature = base64.b64encode(hmac.new(key.encode(), base_string.encode(), hashlib.sha256).digest()).decode()

        # Ajout de la signature aux paramètres OAuth
        oauth_params["oauth_signature"] = signature

        # Création de l'en-tête d'autorisation
  
        oauth_params_header = {
            "oauth_consumer_key": access_key,
            "oauth_signature_method": "HMAC-SHA256",
            "oauth_timestamp": oauth_timestamp,
            "oauth_nonce": oauth_nonce,
            "oauth_version": "1.0",
            "oauth_signature": signature
        }

        auth_header = ", ".join([f'{param}="{urllib.parse.quote(value, safe="")}"' for param, value in oauth_params_header.items()])
   
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Cache-Control": "no-cache",
            "Authorization": f'OAuth {auth_header}',
            "Host": "account.api.here.com"
        }

        # Préparation des données du corps de la requête
        body = {
            "grant_type": "client_credentials"
        }

        # Envoi de la requête POST
        response = post(url, data=body, headers=headers)
        if response.status_code == 200:
            token_json = response.json()
            return token_json["access_token"]
        
    def convert_datetime_to_isoformat(datet):
        return str(datet.isoformat('T') + "Z")
