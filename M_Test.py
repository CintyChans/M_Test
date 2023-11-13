import configparser
from win import *
from numpy import std, array, abs
import serial
import binascii
import serial.tools.list_ports
from threading import *
from log import *
from copy import deepcopy

log = log_file()

plane_std_threshold = 0.024
_header = "57"
default_deque_size = 50
pixels_max = 0.015
center_pixels_accuracy = 0.03
other_pixels_accuracy = 0.05
# 读取配置文件
try:
    config = configparser.ConfigParser()
    config.read("default.ini")

    if config.has_section("Parameter"):
        plane_std_threshold = config.getfloat("Parameter", "plane_std_threshold")
        default_deque_size = config.getint("Parameter", "default_deque_size")
        pixels_max = config.getfloat("Parameter", "pixels_max")
        center_pixels_accuracy = config.getfloat("Parameter", "center_pixels_accuracy")
        other_pixels_accuracy = config.getfloat("Parameter", "other_pixels_accuracy")
    else:
        config.add_section("Parameter")
        config.set(
            section="Parameter",
            option="plane_std_threshold",
            value=str(plane_std_threshold),
        )
        config.set(
            section="Parameter",
            option="default_deque_size",
            value=str(default_deque_size),
        )
        config.set(
            section="Parameter",
            option="pixels_max",
            value=str(pixels_max),
        )
        config.set(
            section="Parameter",
            option="other_pixels_accuracy",
            value=str(other_pixels_accuracy),
        )
        config.set(
            section="Parameter",
            option="center_pixels_accuracy",
            value=str(center_pixels_accuracy),
        )
        config.write(open("default.ini", "w"))
except Exception as e:
    log.error(e)


class PredictModel1(Thread):  # 8x8
    def __init__(self, ser, window):
        super().__init__()
        self.daemon = True
        self.ser = ser
        self.running = True
        self.window = window
        self.data_length = 399
        self.center_pixels = [
            "dis_18",
            "dis_19",
            "dis_20",
            "dis_21",
            "dis_26",
            "dis_27",
            "dis_28",
            "dis_29",
            "dis_34",
            "dis_35",
            "dis_36",
            "dis_37",
            "dis_42",
            "dis_43",
            "dis_44",
            "dis_45",
        ]
        self.start()

    def run(self):
        datastr = _header
        while self.running:
            try:
                data = self.ser.read(1).hex()
                if data != _header:
                    continue
                else:
                    # 解析数据
                    data = self.ser.read(self.data_length).hex()
                    datastr = _header + data
                    dis_data = self.analyse_data(datastr.strip())
                    # 计算平面标准差
                    pixels_deque = deepcopy(self.window.pixels_dis_deque)
                    self.cal_plane_std(list(dis_data.values()))
                    # 计算单独像素点标准差
                    self.cal_pixel_alone_std(pixels_deque)
                    # 64像素点精度检测
                    self.cal_pixel_accaracy_std(pixels_deque)
            except Exception as e:
                log.error(e)

    def cal_pixel_accaracy_std(self, pixels_deque):
        center_accaracy = []
        other_accaracy = []
        for x, y in pixels_deque.items():
            if x in self.center_pixels:
                center_accaracy.append(max(abs(array(y) - 1)))
            else:
                other_accaracy.append(max(abs(array(y) - 1)))
        self.window.accuracy_val.set(round(max(center_accaracy), 4))
        self.window.accuracy_val_2.set(round(max(other_accaracy), 4))

        if (
            max(center_accaracy) <= center_pixels_accuracy
            and max(other_accaracy) <= other_pixels_accuracy
        ):
            self.window.accuracy_res_val.set("通过")
            self.window.accuracy_result.config(fg="black")
        else:
            self.window.accuracy_res_val.set("不通过")
            self.window.accuracy_result.config(fg="red")
            log.debug(
                f"max center_pixels_accuracy = {max(center_accaracy)} ,max other_pixels_accuracy = {max(other_accaracy)}"
            )

    def cal_pixel_alone_std(self, pixels_deque):
        pixels_alone_std = []
        for x, y in pixels_deque.items():
            pixels_alone_std.append(std(y))
        self.window.pixel_alone_std_val.set(round(max(pixels_alone_std), 4))
        if max(pixels_alone_std) < pixels_max:
            self.window.pixel_alone_res_val.set("通过")
            self.window.pixel_alone_result.config(fg="black")
        else:
            self.window.pixel_alone_res_val.set("不通过")
            self.window.pixel_alone_result.config(fg="red")
            log.debug(f"max pixels_alone_std = {max(pixels_alone_std)}")

    def cal_plane_std(self, dis_values):
        plane_std_val = std(dis_values)
        if plane_std_val < plane_std_threshold:
            self.window.plane_result_val.set("通过")
            self.window.plane_result.config(fg="black")
        else:
            self.window.plane_result_val.set("不通过")
            self.window.plane_result.config(fg="red")
        self.window.plane_std_val.set(round(plane_std_val, 4))

    def close(self):
        self.running = False

    # 大小端转换
    def big_small_end_convert(self, data):
        data = binascii.hexlify(binascii.unhexlify(bytes(data.encode()))[::-1])
        return int(data.decode(), 16)

    # 解析串口数据
    def analyse_data(self, data):
        dis_data = {}
        if int(data[:2], 16) == 87:
            zone_map = int(data[16:18], 16)
            index = 18
            for i in range(zone_map):
                dis = self.big_small_end_convert(data[index : index + 6]) / 1000 / 1000
                dis_data["dis_" + str(i)] = dis
                self.window.pixels_dis_deque["dis_" + str(i)].append(dis)
                index += 12
            return dis_data


class MainServer:
    def __init__(self):
        self.window = Window()
        self.window.port_btn.bind("<Button-1>", self.scan_port)
        self.window.connect_btn.bind("<Button-1>", self.connect_port)
        self.window.protocol("WM_DELETE_WINDOW", self.close)
        self.window.deque_size_val.set(default_deque_size)
        self.window.mainloop()

    def scan_port(self, e):
        port_list = list(serial.tools.list_ports.comports())
        port = [i[0] for i in port_list]
        try:
            self.window.port_box["value"] = port
            self.window.port_box.current(0)
        except Exception as e:
            log.error(e)
            self.window.port_box["value"] = [""]
            self.window.port_box.current(0)

    def connect_port(self, e):
        try:
            if not self.window.connecting:
                self.port = serial.Serial(
                    self.window.port_box.get(), self.window.baudrateval.get()
                )
                self.window.connecting = True
                self.window.init_deque()
                self.program = PredictModel1(self.port, self.window)
                self.window.connect_btn.config(bg="#75bbfd", text="关闭串口")
            else:
                self.window.connecting = False
                self.program.close()
                self.port.close()
                self.window.connect_btn.config(bg="white", text="连接串口")
        except Exception as e:
            log.error(e)

    def close(self):
        try:
            config.set(
                section="Parameter",
                option="default_deque_size",
                value=str(self.window.deque_size_val.get()),
            )
            config.write(open("default.ini", "w"))
            self.window.quit()
            self.window.destroy()
            self.port.close()
            self.program.close()
            log.close()
        except Exception as e:
            log.error(e)


MainServer()
