import mysql.connector

dataBase = mysql.connector.connect(
    host="localhost",
    user="dcrm",
    passwd="dcrm",
)

cursorObject = dataBase.cursor()

cursorObject.execute("CREATE DATABASE dcrm")

print("Database Created Successfully !!")