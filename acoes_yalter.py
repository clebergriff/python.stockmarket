# encoding: utf-8

import mysql.connector
import time
import json
import requests
import datetime
import array
import re
from bs4 import BeautifulSoup

def find_between(s, start, end):
    try:        
        return (re.findall("%s.+?%s" % (re.escape(start), re.escape(end)), s)[0])
    except Exception: 
        return None

def watchActives():    

    mydb = mysql.connector.connect(
      host="localhost",
      user="python",
      passwd="python",
      database='yalter'
    )

    ativos = mydb.cursor(dictionary=True)

    ativos.execute("SELECT ativos.nome, valores.valor, valores.`data`, TIMESTAMPDIFF(MINUTE,"
        +" IFNULL(MAX(valores.`data`), '2000-01-01'), NOW()) AS ult_alt"
        +" FROM ativos"
        +" LEFT JOIN valores ON ativos.nome = valores.simbolo"
        +" WHERE ativos.ignorar = 0"
        +" GROUP BY ativos.nome"
        +" HAVING ult_alt > 5"
        +" ORDER BY ult_alt DESC")

    ativos = ativos.fetchall()

    valores = mydb.cursor(dictionary=True)

    for row in ativos:
        print('Analysing stock: %s' % (row["nome"]))
        
        page = requests.get("https://www.google.com/search?q=" +row["nome"])

        if page.status_code == 200:
            soup = BeautifulSoup(page.text, "lxml")
            
            start = 'Preço das ações'
            end = ' '
            
            valor = find_between(soup.get_text(), start, end)
            
            if valor is None:
                print('Stock %s not found' % (row["nome"]))
                
                sql = ("UPDATE ativos SET ignorar = 1 WHERE nome = '%s'" % (row["nome"]))
                valores.execute(sql)
                mydb.commit()
                
                continue
            
            valor = int("".join(filter(str.isdigit, valor)))
            # valor = float(filter(str.isdigit, valor))
            valor = float(valor/100)
            
            sql = "INSERT INTO valores(simbolo, valor) VALUES (%s, %s)"
            params = (row["nome"], valor)
            valores.execute(sql, params)
            mydb.commit()
            
            print('[%s] Value saved: R$ %s' % (row["nome"], valor))              
        else:
            print("HTTP error: " +str(page.status_code))
        
        time.sleep(3)

while True:
    print("Starting stock market fetching..")
    watchActives()
    print("Next fetching in 60 seconds...")
    time.sleep(60)