import mysql.connector

mydb = mysql.connector.connect(
  host="localhost",
  user="root",
  passwd="PASSword123",
  auth_plugin='mysql_native_password'
)

my_cursor = mydb.cursor()

# my_cursor.execute("CREATE DATABASE blog")

my_cursor.execute("SHOW DATABASES")

if __name__ == '__main__':
  for x in my_cursor:
    print(x)