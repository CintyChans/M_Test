import configparser
from win import *
from numpy import std, array, linspace, meshgrid, zeros
import serial
import binascii
import serial.tools.list_ports
from threading import *
from log import *

threshold = 0.024
_header = '57'

# *_pos 为数据部分切片位置,*_length为数据部分长度
_frame_header = 87
_frame_header_pos = 2
_function_mark_pos = _frame_header_pos+2
_reserved_pos = _function_mark_pos+2
_id_length_pos = _reserved_pos+2
_system_time_pos = _id_length_pos+8
_zone_map_pos = _system_time_pos+2
_sumcheck_pos = -2
_dis_pos = 6
_dis_status_pos = _dis_pos+2
_signal_strength_pos = _dis_status_pos+4
_dis_data_length = 12
_reserved1_length = 12


# 读取配置文件
try:
    config = configparser.ConfigParser()
    config.read('default.ini')

    if config.has_section('Parameter'):
        threshold = config.getfloat('Parameter', 'threshold')
    else:
        config.add_section('Parameter')
        config.set(section='Parameter', option='threshold',
                   value=str(threshold))
        config.write(open('default.ini', 'w'))
except:
    pass


class PredictModel1(Thread):  # 8x8
    def __init__(self, ser, window):
        super().__init__()
        self.daemon = True
        self.ser = ser
        self.running = True
        self.window = window
        self.data_length = 399
        self.start()

    def run(self):
        datastr = _header
        while self.running:
            data = self.ser.read(1).hex()
            if data != _header:
                continue
            else:
                data = self.ser.read(self.data_length).hex()
                datastr = _header+data
                _, l = self.analyse_data(datastr.strip())
                self.window.Z = l[::, :1].reshape(8, 8)
                stdval = std(l[::, :1].reshape(-1))
                if stdval < threshold:
                    self.window.predictval.set('是')
                else:
                    self.window.predictval.set('否')
                self.window.stdval.set(round(stdval, 4))

    def close(self):
        self.running = False

# 大小端转换
    def big_small_end_convert(self, data):
        data = binascii.hexlify(binascii.unhexlify(bytes(data.encode()))[::-1])
        return int(data.decode(), 16)

# 解析串口数据
    def analyse_data(self, data):
        after_data = {}
        after_data['frame_header'] = int(data[:_frame_header_pos], 16)
        if after_data['frame_header'] == _frame_header:
            after_data['function_mark'] = int(
                data[_frame_header_pos:_function_mark_pos], 16)
            after_data['reserved'] = int(
                data[_function_mark_pos:_reserved_pos], 16)
            after_data['id'] = int(data[_reserved_pos:_id_length_pos], 16)
            after_data['system_time'] = self.big_small_end_convert(
                data[_id_length_pos:_system_time_pos])
            after_data['zone_map'] = int(
                data[_system_time_pos:_zone_map_pos], 16)
            after_data['data'] = {}
            index = _zone_map_pos
            data_list = []
            for i in range(after_data['zone_map']):
                dis = self.big_small_end_convert(data[index:index+6])/1000/1000
                dis_status = int(
                    data[index+_dis_pos:index+_dis_status_pos], 16)
                signal_strength = self.big_small_end_convert(
                    data[index+_dis_status_pos:index+_signal_strength_pos])
                after_data['data']['data'+str(i)] = {
                    'dis': dis, 'dis_status': dis_status, 'signal_strength': signal_strength}
                data_list.append([dis, dis_status, signal_strength])
                index += _dis_data_length

            after_data['reserved1'] = self.big_small_end_convert(
                data[index:index+_reserved1_length])
            after_data['sumcheck'] = int(data[_sumcheck_pos:], 16)
            return after_data, array(data_list)
        else:
            return None, None


class PredictModel2(Thread):  # 4x4
    def __init__(self, ser, window):
        super().__init__()
        self.daemon = True
        self.ser = ser
        self.running = True
        self.window = window
        self.data_length = 111
        self.start()

    def run(self):
        datastr = _header
        while self.running:
            data = self.ser.read(1).hex()
            if data != _header:
                continue
            else:
                data = self.ser.read(self.data_length).hex()
                datastr = _header+data
                _, l = self.analyse_data(datastr.strip())
                self.window.Z = l[::, :1].reshape(4, 4)
                stdval = std(l[::, :1].reshape(-1))
                if stdval < threshold:
                    self.window.predictval.set('是')
                else:
                    self.window.predictval.set('否')
                self.window.stdval.set(round(stdval, 4))

    def close(self):
        self.running = False

    def big_small_end_convert(self, data):
        data = binascii.hexlify(binascii.unhexlify(bytes(data.encode()))[::-1])
        return int(data.decode(), 16)

    def analyse_data(self, data):
        after_data = {}
        after_data['frame_header'] = int(data[:_frame_header_pos], 16)
        if after_data['frame_header'] == _frame_header:
            after_data['function_mark'] = int(
                data[_frame_header_pos:_function_mark_pos], 16)
            after_data['reserved'] = int(
                data[_function_mark_pos:_reserved_pos], 16)
            after_data['id'] = int(data[_reserved_pos:_id_length_pos], 16)
            after_data['system_time'] = self.big_small_end_convert(
                data[_id_length_pos:_system_time_pos])
            after_data['zone_map'] = int(
                data[_system_time_pos:_zone_map_pos], 16)
            after_data['data'] = {}
            index = _zone_map_pos
            data_list = []
            for i in range(after_data['zone_map']):
                dis = self.big_small_end_convert(
                    data[index:index+_dis_pos])/1000/1000
                dis_status = int(
                    data[index+_dis_pos:index+_dis_status_pos], 16)
                signal_strength = self.big_small_end_convert(
                    data[index+_dis_status_pos:index+_signal_strength_pos])
                after_data['data']['data'+str(i)] = {
                    'dis': dis, 'dis_status': dis_status, 'signal_strength': signal_strength}
                data_list.append([dis, dis_status, signal_strength])
                index += _dis_data_length

            after_data['reserved1'] = self.big_small_end_convert(
                data[index:index+_reserved1_length])
            after_data['sumcheck'] = int(data[_sumcheck_pos:], 16)
            return after_data, array(data_list)
        else:
            return None, None


class MainServer():
    def __init__(self):
        self.window = Window()
        self.logfile = log_file()
        self.window.port_btn.bind('<Button-1>', self.scan_port)
        self.window.connect_btn.bind('<Button-1>', self.connect_port)
        self.window.protocol('WM_DELETE_WINDOW', self.close)
        self.window.mainloop()

    def scan_port(self, e):
        port_list = (list(serial.tools.list_ports.comports()))
        port = [i[0] for i in port_list]
        try:
            self.window.port_box['value'] = port
            self.window.port_box.current(0)
        except Exception as e:
            self.logfile.error(e)
            self.window.port_box['value'] = ['']
            self.window.port_box.current(0)

    def connect_port(self, e):
        try:
            if not self.window.connecting:
                self.port = serial.Serial(
                    self.window.port_box.get(), self.window.baudrateval.get())
                self.window.connecting = True
                self.check_pixel()
                self.window.connect_btn.config(bg='#75bbfd', text='关闭串口')
            else:
                self.window.connecting = False
                self.program.close()
                self.port.close()
                self.window.connect_btn.config(bg='white', text='连接串口')
        except Exception as e:
            self.logfile.error(e)

    def check_pixel(self):
        if self.window.pixel.get() == '8x8':
            X = linspace(0, 8, 8)
            self.window.Z = zeros((8, 8))
            self.window.X, self.window.Y = meshgrid(X, X)
            self.program = PredictModel1(self.port, self.window)
        else:
            X = linspace(0, 4, 4)
            self.window.X, self.window.Y = meshgrid(X, X)
            self.window.Z = zeros((4, 4))
            self.program = PredictModel2(self.port, self.window)

    def close(self):
        try:
            self.window.quit()
            self.window.destroy()
            self.port.close()
            self.program.close()
            self.logfile.close()
        except Exception as e:
            self.logfile.error(e)


MainServer()
