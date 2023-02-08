from win import *
from numpy import std,array,linspace,meshgrid,zeros
import serial
import time
import binascii
import serial.tools.list_ports
from threading import *
from log import *

threshold=0.0135

import configparser
try:
    config = configparser.ConfigParser()
    config.read('default.ini')

    if config.has_section('Parameter'):
        threshold=config.getfloat('Parameter', 'threshold')
    else:
        threshold=0.0135  
        config.add_section('Parameter')
        config.set(section='Parameter',option='threshold',value=str(threshold))
        config.write(open('default.ini', 'w'))
except:
    pass


class PredictModel1(Thread):
    def __init__(self,ser,window):
        super().__init__()
        self.daemon=True
        self.ser=ser
        self.running=True
        self.window=window
        self.start()

    def run(self):
        datastr='57'
        while self.running:
            data=self.ser.read(1).hex()
            if data!='57':
                continue
            else:
                data=self.ser.read(399).hex()
                datastr='57'+data
                d,l=self.analyse_data(datastr.strip())       
                self.window.Z=l[::,:1].reshape(8,8)  
                stdval=std(l[::,:1].reshape(-1))
                if stdval<threshold:
                    self.window.predictval.set('是')
                else:
                    self.window.predictval.set('否')
                self.window.stdval.set(round(stdval,4))
                

    def close(self):
        self.running=False

    def big_small_end_convert(self,data):
        data= binascii.hexlify(binascii.unhexlify(bytes(data.encode()))[::-1])
        return int(data.decode(),16)

    def analyse_data(self,data):
        after_data={}
        after_data['frame_header']=int(data[:2],16)
        if after_data['frame_header']==87:
            after_data['function_mark']=int(data[2:4],16)
            after_data['reserved']=int(data[4:6],16)
            after_data['id']=int(data[6:8],16)
            after_data['system_time']=self.big_small_end_convert(data[8:16])
            after_data['zone_map']=int(data[16:18],16)
            after_data['data']={}
            index=18
            data_list=[]
            for i in range(after_data['zone_map']):
                dis=self.big_small_end_convert(data[index:index+6])/1000/1000
                dis_status=int(data[index+6:index+8],16)
                signal_strength=self.big_small_end_convert(data[index+8:index+12])
                after_data['data']['data'+str(i)]={'dis':dis,'dis_status':dis_status,'signal_strength':signal_strength}
                data_list.append([dis,dis_status,signal_strength])
                index+=12
        
            after_data['reserved1']=self.big_small_end_convert(data[index:index+12])
            after_data['sumcheck']=int(data[-2:],16)
            return after_data,array(data_list)
        else:
            return None,None


class PredictModel2(Thread):
    def __init__(self,ser,window):
        super().__init__()
        self.daemon=True
        self.ser=ser
        self.running=True
        self.window=window
        self.start()

    def run(self):
        datastr='57'
        while self.running:
            data=self.ser.read(1).hex()
            if data!='57':
                continue
            else:
                data=self.ser.read(111).hex()
                datastr='57'+data
                d,l=self.analyse_data(datastr.strip())       
                self.window.Z=l[::,:1].reshape(4,4)  
                stdval=std(l[::,:1].reshape(-1))
                if stdval<threshold:
                    self.window.predictval.set('是')
                else:
                    self.window.predictval.set('否')
                self.window.stdval.set(round(stdval,4))

    def close(self):
        self.running=False

    def big_small_end_convert(self,data):
        data= binascii.hexlify(binascii.unhexlify(bytes(data.encode()))[::-1])
        return int(data.decode(),16)

    def analyse_data(self,data):
        after_data={}
        after_data['frame_header']=int(data[:2],16)
        if after_data['frame_header']==87:
            after_data['function_mark']=int(data[2:4],16)
            after_data['reserved']=int(data[4:6],16)
            after_data['id']=int(data[6:8],16)
            after_data['system_time']=self.big_small_end_convert(data[8:16])
            after_data['zone_map']=int(data[16:18],16)
            after_data['data']={}
            index=18
            data_list=[]
            for i in range(after_data['zone_map']):
                dis=self.big_small_end_convert(data[index:index+6])/1000/1000
                dis_status=int(data[index+6:index+8],16)
                signal_strength=self.big_small_end_convert(data[index+8:index+12])
                after_data['data']['data'+str(i)]={'dis':dis,'dis_status':dis_status,'signal_strength':signal_strength}
                data_list.append([dis,dis_status,signal_strength])
                index+=12
        
            after_data['reserved1']=self.big_small_end_convert(data[index:index+12])
            after_data['sumcheck']=int(data[-2:],16)
            return after_data,array(data_list)
        else:
            return None,None

class MainServer():
    def __init__(self):
        self.window=Window()
        self.logfile=log_file()
        self.window.port_btn.bind('<Button-1>',self.scan_port)
        self.window.connect_btn.bind('<Button-1>',self.connect_port)
        self.window.protocol('WM_DELETE_WINDOW', self.close)
        self.window.mainloop()

    def scan_port(self,e):
        port_list=(list(serial.tools.list_ports.comports()))
        port=[i[0] for i in port_list]
        try:
            self.window.port_box['value'] = port
            self.window.port_box.current(0)
        except Exception as e:
            self.logfile.add(e)
            self.window.port_box['value'] =['']
            self.window.port_box.current(0)

    def connect_port(self,e):
        try:
            if not self.window.connecting:
                self.port=serial.Serial(self.window.port_box.get(), self.window.baudrateval.get())
                self.window.connecting=True
                self.check_pixel()
                self.window.connect_btn.config(bg='#75bbfd',text='关闭串口')
            else:
                self.window.connecting=False
                self.program.close()
                self.port.close()
                self.window.connect_btn.config(bg='white',text='连接串口')
        except Exception as e:
            self.logfile.add(e)


    def check_pixel(self):
        if self.window.pixel.get()=='8x8':
            X= linspace(0, 8,8)
            self.window.Z=zeros((8,8))
            self.window.X,self.window.Y=meshgrid(X,X)
            self.program=PredictModel1(self.port,self.window)
        else:
            X= linspace(0, 4,4)
            self.window.X,self.window.Y=meshgrid(X,X)
            self.window.Z=zeros((4,4))
            self.program=PredictModel2(self.port,self.window)



    def close(self):
        try:
            self.window.quit()
            self.window.destroy()  
            self.port.close()
            self.program.close()
            self.logfile.close()
        except Exception as e:
            self.logfile.add(e)

        
        
        
MainServer()
