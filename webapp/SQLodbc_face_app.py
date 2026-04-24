import pyodbc
#driver= '{SQL Server Native Client 11.0}'

#Driver = "{SQL Server}"
#config.SQL_SERVER

class SqlODBC:
    def __init__(self, db, table):
        self.DATABASE = db
        self.TABLENAME = table

    def setDB_Params(self):
        "set database parameters"
        self.Server = "KFTAPPSVR\KFTSQLSVR"
        if self.TABLENAME == 'Model_Data':
            self.Driver = "{SQL Server Native Client 11.0}"
        else:
            self.Driver = "{SQL Server}"
        self.UID = "ds.user"
        self.PWD = "ds@12435"
        
        #Switch if DB1,2,3,4,5 = SQL_SVR1, UID_SVR1, PWD_SVR1 | DB6,7,8, = SQL_SVR2
        #self.Server | self.UID
        return True
    
    def connectDB(self):
        "connect with sql using pyodbc"
        cs = ("DRIVER=" + self.Driver + ";" + "SERVER=" + self.Server + ";" + "UID=" + self.UID + ";" + "PWD=" + self.PWD + ";" +  "Database=" + self.DATABASE + ";" )
        #print(cs)
        self.cnxn = pyodbc.connect(cs)
        self.cursor = self.cnxn.cursor()
        return True

    def disconnectDB(self):
        "disconnect connection with sql"
        self.cnxn.close()

    def get_data(self):
        "get data from table"
        data_array = []
        print(" self.TABLENAME ", self.TABLENAME )
        
        #print("SELECT " + query1 + " FROM dbo." + self.TABLENAME + " " + query2)
        self.cursor.execute('SELECT * FROM dbo.' + self.TABLENAME)
        #self.cursor.execute("SELECT TradeDate, TradeTime,TradePrice FROM dbo.CCIL_IDdata where ISIN = 'IN0020190362' and Tag = 'NRML' order by TradeDate, TradeTime")
        dataSet = self.cursor.fetchall()
       
        for row in dataSet:
            data_array.append([x for x in row])
            #data_array.append(list(row))
        return data_array
       
    def log_update(self,log_date,log_level,logs):
        "insert model details in sql"
        print("logs from SQLodbc_face_app",logs)
        query = """INSERT INTO dbo.""" + self.TABLENAME + """ (Dates,Levels,Log_Message) 
        VALUES (?,?,?)""" 
        #query = """UPDATE dbo.""" + self.TABLENAME + """SET Face_Logs = """ +logs  
        params = (log_date,log_level,logs)
        self.cursor.execute(query,params)
        self.cnxn.commit()
    
    
