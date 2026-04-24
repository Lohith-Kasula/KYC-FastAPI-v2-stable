# -*- coding: utf-8 -*-
"""
Created on Wed May  6 12:11:53 2020

@author: hasik
"""
import SQLodbc_face_app
import pandas as pd
from datetime import date 

class DBcaller():
    def get_data():
        dbconnect = SQLodbc_face_app.SqlODBC(db ='PY_DB', table = 'Face_App_Logs')
        dbconnect.setDB_Params()
        dbconnect.connectDB()
        sqldata = dbconnect.get_data()
        data = pd.DataFrame(sqldata,columns = ['Dates','Levels','Log_Message'])
        data[data['Dates'] == date.today()]
        #data.columns = ['Dates,Levels,Log_Message']
        # data.set_index('DtTime',drop = True, inplace = True)
        dbconnect.disconnectDB
        return data
                   
    def update_logs(log_date,log_level,logs):
        "insert new trained model in sql"
        print("logs from dbcaller_face_app: ",logs)
        dbconnect = SQLodbc_face_app.SqlODBC(db ='PY_DB', table = 'Face_App_Logs')
        dbconnect.setDB_Params()
        dbconnect.connectDB()
        dbconnect.log_update(log_date,log_level,logs)
        dbconnect.disconnectDB()

