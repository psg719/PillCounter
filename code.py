from sqlite3.dbapi2 import Error
import serial
import sqlite3
import time
import dropbox
import os
from PIL import Image

#connect to sqlite db
conn = sqlite3.connect('drugapr21.sqlite',check_same_thread=False)

#connect to dropbox
access_token = input("Enter your Dropbox access token here")
dbx = dropbox.Dropbox(access_token)

#directory
directory = os.getcwd()



def count():
    med_barcode = str(input("Please scan medication barcode..."))

    #getting tablet name from sql table
    get_name(med_barcode)
    print(drug_name)
    #getting tablet weight from sql table
    get_weight(med_barcode)
    if med_weight is None:
        choice = input('Medication weight is not stored, would you like to set it? (Y/N)')
        if choice.lower().startswith('y'):
            set()
            count()
        else:
            initial_program()

    if drug_name is None:
        input('Unfortunately this drug is not in the database...please count manually')
        initial_program()
    print(drug_name)
    input('Please place counting cup then press Tare/Zero on scale now then press "Enter"...')
    serialPort = serial.Serial(
    port="COM3", baudrate=9600, bytesize=8, timeout=2, stopbits=serial.STOPBITS_ONE)
    serialString = ""  # Used to hold data coming over UART
    try:
        while 1:
            # Wait until there is data waiting in the serial buffer
            if serialPort.in_waiting > 0:
                # Read data out of the buffer until a carraige return / new line is found
                serialString = serialPort.readline()
                # Print the contents of the serial data
                try:    
                    dirty_str = serialString.decode("Ascii")
                    #print(dirty_str)
                    clean_str_1 = dirty_str.replace(" ","").replace("g","").replace("M","")
                    clean_str_2 = clean_str_1[2:]
                    #print(clean_str_2)
                    tablets = float(clean_str_2) / float(med_weight)
                    print(drug_name,'......................', int(tablets),"tablets")
                except Exception as ex:
                    #print(ex)
                    pass
    except KeyboardInterrupt:
        serialPort.close()
        initial_program()
        

def set():
    med_barcode = str(input("Please scan medication barcode..."))
    get_name(med_barcode)
    get_weight(med_barcode)
    print(drug_name)
    print("weight =",med_weight,"grams")
    input('Please place counting cup then press Tare/Zero on scale now then press "Enter"...')
    input("Place **20** tablets in counting cup then press 'Enter'...")
    #Opening COM port
    serialPort = serial.Serial(
    port="COM3", baudrate=9600, bytesize=8, timeout=2, stopbits=serial.STOPBITS_ONE)
    serialString = ""  # Used to hold data coming over UART
    lst_weight = []
    while len(lst_weight) < 50:
        # Wait until there is data waiting in the serial buffer
        if serialPort.in_waiting > 0:
            # Read data out of the buffer until a carraige return / new line is found
            serialString = serialPort.readline()
            # Print the contents of the serial data
            try:    
                dirty_str = serialString.decode("Ascii")
                clean_str_1 = dirty_str.replace(" ","").replace("g","").replace("M","")
                clean_str_2 = clean_str_1[2:]
                lst_weight.append(clean_str_2)
            except:
                pass
    #print(lst_weight)
    lst_weight_f = [float(x) for x in lst_weight if x]
    print(lst_weight_f)
    weight_avg = sum(lst_weight_f)/len(lst_weight_f)
    new_med_weight = round(weight_avg / 20, 2)

    #gets old weight to compare with new one
    get_weight(med_barcode)
    #gets pill name
    get_name(med_barcode)
    if drug_name is None:
        input('Unfortunately this drug is not in the database...please count manually. Press enter to continue...')
        initial_program()
    
    print("Are you sure you want to update", drug_name,"weight from",med_weight,"to",new_med_weight,"? Y/N...")
    choice = input('...')
    if choice.lower().startswith('y') :
        conn.execute("UPDATE dpd SET weight = ? WHERE (UPC = ?)",(new_med_weight,med_barcode,))
        conn.commit()
        input(drug_name+" weight has been updated to "+str(new_med_weight))
    else:
        input('medication weight has NOT been updated, press "Enter" to continue...')
        pass
    serialPort.close()
    initial_program()


def check_rx():
    rx_barcode = str(input("Please scan prescription barcode..."))
    input('Press enter...')
    med_barcode = str(input("Please scan medication barcode..."))
    input('Press enter...')
    try:
        #get din from rx barcode
        rx_din = rx_barcode[:8]
        #programing going here
        get_din(rx_din)
        din_jpg = rx_din+'.jpg'
        rx_din_1 = rx_din
        

        #get din from med barcode
        get_din(med_barcode)
        scanned_din = din
        if rx_din.isnumeric() and med_barcode.isnumeric():
            if rx_din_1 == scanned_din:
                get_name(med_barcode)
                input("You've matched the correct drug for the prescription! \n"+drug_name)
                try:
                    dbx.files_download_to_file(directory+'/images/'+din_jpg,'/good_images/'+din_jpg)
                    im = Image.open(directory+'/images/'+din_jpg)
                    im.show()
                except Exception as ex:
                    print(ex)
                    pass
   
                print(med_barcode)
                get_weight(med_barcode)
                print(med_weight)
                if med_weight is None:
                    choice = input('You need to set weight for this pill before counting. Would you like to set weight for this tablet?')
                    if choice.lower().startswith('y'):
                        set()
                        count()
                else:
                    count()
            else:
                input("You've selected the wrong drug for this prescription, please double check the DIN number and try again")
                pass
            
        else:
            pass
    except Exception as ex:
        print(ex)
        input('DIN number not available...')
        pass
    initial_program()
    

def initial_program():
    while True:
        choice = input('\n\n\nTo Count Tablets press 1 and hit "Enter"...\nTo Set tablet weight press 2 and hit "Enter"...\n')#To check RX press 3 and hit "Enter"...\n...')
        if choice == '1':
            count()
        elif choice == '2':
            set()
        else:
            print("You've entered an invalid choice")

def get_weight(med_barcode):
    global med_weight
    try:
        weight_sql = conn.execute("SELECT weight from dpd WHERE (UPC = ?)",(med_barcode,))
        for i in weight_sql:
            i = list(i)
            break
        med_weight = i[0]
    except:
        input("Sorry, medication not found in database! Press enter to continue...")
        initial_program() 
    

def get_name(med_barcode):
    global drug_name
    try:
        name_sql = conn.execute("SELECT drug from dpd WHERE (UPC = ?)",(med_barcode,))
        
        for i in name_sql:
            i = list(i)
            break
        drug_name = i[0]
    except:
        input("Sorry! Drug not found in database. Press enter to continue...")
        initial_program()
        
    
def get_din(UPC):
    global din
    try:
        rx_din_sql = conn.execute("SELECT DIN from dpd WHERE (UPC = ?)",(UPC,))
        for i in rx_din_sql:
            i = list(i)
            break
        din = i[0]
    except Exception as ex:
        #print(ex)
        din = None

if __name__ == "__main__":
    initial_program()
