import datetime
import json
import os
from pathlib import Path
import sqlite3
import requests
from os.path import exists


os.chdir(Path(__file__).parent)

class Weather:

    def __init__(self):

        if not exists("weather_data.db"):
            self. conn = self.create_connection()
            self.create_table(self.conn)
        else:
            self. conn = self.create_connection()

        self.date = datetime.date.today()
    

    def create_connection(self):
        conn = sqlite3.connect("weather_data.db")
        return conn
        
    def get_weather(self, city):
        with open('config.json') as f:
            config = json.load(f)
            api_key = config['api_key']
            lang = config['lang']
            unit = config['unit']
            url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&units={unit}&lang={lang}&appid={api_key}"
            response = requests.get(url)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Error retrieving weather data for {city}: {response.text}")
                return None


    def get_weather_data(self):
        array = []
        city = input("Enter city: ")
        weather = self.get_weather(city)
        if weather is not None:
            
            min_temperature = weather['main']['temp_min']
            max_temperature = weather['main']['temp_max']
            temperature = weather['main']['temp']
            array = [city, min_temperature, max_temperature, temperature, self.date]
            return array
        return None
  


    def create_table(self, conn):
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE cities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cityName TEXT,
                active INTEGER 
            )
        """)
        cursor.execute("""
            CREATE TABLE weather (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                city_id INTEGER,
                temperature REAL,
                min_temperature REAL,
                max_temperature REAL,
                date DATE,
                FOREIGN KEY (city_id) REFERENCES cities (id)
            )
        """)
        conn.commit()


    def insert_city(self, conn, cityName, active):
        cursor = conn.cursor()
        cursor.execute("INSERT INTO cities (cityName, active) VALUES (?,?)", (cityName, active))
        conn.commit()

    def get_active_cities(self, conn):
        arrayResult  = []
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM cities WHERE active = 1")
        cursorResults = cursor.fetchall()

        for cursorResult in cursorResults:
            cursor.execute("SELECT * FROM weather WHERE city_id = ?", (cursorResult[0],))
            cursorResult = [cursorResult[1], cursor.fetchall()]
            arrayResult.append(cursorResult)

        return arrayResult
    
    def get_active_city(self, conn, cityName):
        arrayResult  = []
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM cities WHERE active = 1 and cityName = ?", (cityName,))
        cursorResult = cursor.fetchone()

        cursor.execute("SELECT * FROM weather WHERE city_id = ?", (cursorResult[0],))
        cursorResult = [cursorResult[1], cursor.fetchall()]
        arrayResult.append(cursorResult)

        return arrayResult
        

    def check_existing_records(self, conn, date, city_id):
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM weather WHERE date = ? AND city_id = ?
        """, (date, city_id))
        return cursor.fetchall()
    
    def get_city_id (self, conn, cityName):
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM cities WHERE cityName = ? AND active = 1", (cityName,))
        return cursor.fetchone()
    
    def delete_old_record(self, conn, cityName):
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE cities SET active = 0 WHERE cityName = ? and active = 1
        """, (cityName,))
        conn.commit()

    def print_Actives_Cities_Informations(self, arrays):
        print ()
        print ("#################################################################")
        for array in arrays:
            print ("city:", array[0],"\t", "Date:", array[1][0][5], "\t", "Minimum temperature:", array[1][0][2], "\t", "Maximum temperature:", array[1][0][3], "\t", "Temperature:", array[1][0][4])
        print ("#################################################################")
        print ()

    def insert_weather_data(self, conn, city_id, temperature, min_temperature, max_temperature, date):
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO weather (city_id, temperature, min_temperature, max_temperature, date)
            VALUES (?, ?, ?, ?, ?)
        """, (city_id, temperature, min_temperature, max_temperature, date))
        conn.commit()

    def main (self):
        while True:
            print ("########################## Welcome ################################")
            array_weather_data = None
            array_weather_data = self.get_weather_data()
            if array_weather_data is not None:
                get_cityID = self.get_city_id(self.conn, array_weather_data[0])
                if get_cityID is not None:
                    result_check_existing_records = self.check_existing_records(self.conn, self.date, get_cityID[0])
                    if result_check_existing_records != []:
                        input_user = None
                        while True:
                            print ("The request has already been completed for today and is already stored in the DB ...\n")
                            print ("Press \'1\' to delete the old record and insert the new records")
                            print ("Press \'2\' to keep the old records and ignore the new responsed data")
                            input_user = input()
                            if input_user == "1" or input_user == "2":
                                break
                        if input_user == "1":
                            self.delete_old_record(self.conn, array_weather_data[0])
                            self.insert_city(self.conn, array_weather_data[0], 1)
                            
                            get_cityID = self.get_city_id(self.conn, array_weather_data[0])
                            self.insert_weather_data(self.conn, get_cityID[0], array_weather_data[1], array_weather_data[2], array_weather_data[3], array_weather_data[4])
                            result__active_city = self.get_active_city(self.conn, array_weather_data[0])
                            self.print_Actives_Cities_Informations(result__active_city)
                        elif input_user == "2":
                            result__active_city = self.get_active_city(self.conn, array_weather_data[0])
                            self.print_Actives_Cities_Informations(result__active_city)
                    
                else:
                    self.insert_city(self.conn, array_weather_data[0], 1)
                    get_cityID = self.get_city_id(self.conn, array_weather_data[0])
                    self.insert_weather_data(self.conn, get_cityID[0], array_weather_data[1], array_weather_data[2], array_weather_data[3], array_weather_data[4])
                    result__active_city = self.get_active_city(self.conn, array_weather_data[0])
                    self.print_Actives_Cities_Informations(result__active_city)


                print ()
                while True:
                    print ("Press \'A\' or \'a\' to get all actives cities informations or \'C\' or \'c\' to continue !")
                    input_user_new = input()
                    if input_user_new == "C" or input_user_new == "c" or input_user_new == "A" or input_user_new == "a":
                        break
            
                if input_user_new == "C" or input_user_new == "c":
                    pass
                elif input_user_new == "A" or input_user_new == "a":
                    result__active_cities = self.get_active_cities(self.conn)
                    self.print_Actives_Cities_Informations(result__active_cities)
            

            print ()
            input_User = None
            while True:
                print ("Do you want to continue ? y, Y/ n, N")
                input_User = input()
                if input_User == "y" or input_User == "Y" or input_User == "n" or input_User == "N":
                    break
            
            if input_User == "y" or input_User == "Y":
                continue
            elif input_User == "n" or input_User == "N":
                print ("goodbye see you next time ...")
                break


if __name__== "__main__":
    weather = Weather()
    weather.main()
    