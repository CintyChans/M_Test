import binascii
from numpy import std, array, abs, ptp
from copy import deepcopy
from threading import *
from env import log, _header, _function_mark, _data_length, _frame_header
from serial import SerialException


class TOFSENSE_M(Thread):  # 8x8
    def __init__(self, ser, window, data):
        super().__init__()
        self.daemon = True
        self.ser = ser
        self.running = True
        self.TOFSense_M_MS_TAB = window
        self.default_data = data
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
                    pixels_deque = deepcopy(self.TOFSense_M_MS_TAB.pixels_dis_deque)
                    self.cal_plane_std(list(dis_data.values()))
                    # 计算单独像素点标准差
                    self.cal_pixel_alone_std(pixels_deque)
                    # 64像素点精度检测
                    self.cal_pixel_accaracy(pixels_deque)
            except SerialException as e:
                self.close()
                log.error(e)
            except Exception as e:
                log.error(e)

    def cal_pixel_accaracy(self, pixels_deque):
        center_accaracy = []
        other_accaracy = []
        for x, y in pixels_deque.items():
            if x in self.center_pixels:
                center_accaracy.append(max(abs(array(y) - 1)))
            else:
                other_accaracy.append(max(abs(array(y) - 1)))
        self.TOFSense_M_MS_TAB.accuracy_val.set(round(max(center_accaracy), 4))
        self.TOFSense_M_MS_TAB.accuracy_val_2.set(round(max(other_accaracy), 4))

        if (
            max(center_accaracy) <= self.default_data["center_pixels_accuracy"]
            and max(other_accaracy) <= self.default_data["other_pixels_accuracy"]
        ):
            self.TOFSense_M_MS_TAB.accuracy_res_val.set("通过")
            self.TOFSense_M_MS_TAB.accuracy_result.config(fg="black")
        else:
            self.TOFSense_M_MS_TAB.accuracy_res_val.set("不通过")
            self.TOFSense_M_MS_TAB.accuracy_result.config(fg="red")
            # log.debug(
            #     f"max center_pixels_accuracy = {max(center_accaracy)} ,max other_pixels_accuracy = {max(other_accaracy)}"
            # )

    def cal_pixel_alone_std(self, pixels_deque):
        pixels_alone_std = []
        for x, y in pixels_deque.items():
            pixels_alone_std.append(std(y))
        self.TOFSense_M_MS_TAB.pixel_alone_std_val.set(round(max(pixels_alone_std), 4))
        if max(pixels_alone_std) < self.default_data["pixels_max"]:
            self.TOFSense_M_MS_TAB.pixel_alone_res_val.set("通过")
            self.TOFSense_M_MS_TAB.pixel_alone_result.config(fg="black")
        else:
            self.TOFSense_M_MS_TAB.pixel_alone_res_val.set("不通过")
            self.TOFSense_M_MS_TAB.pixel_alone_result.config(fg="red")
            # log.debug(f"max pixels_alone_std = {max(pixels_alone_std)}")

    def cal_plane_std(self, dis_values):
        plane_std_val = std(dis_values)
        if plane_std_val < self.default_data["plane_std_threshold"]:
            self.TOFSense_M_MS_TAB.plane_result_val.set("通过")
            self.TOFSense_M_MS_TAB.plane_result.config(fg="black")
        else:
            self.TOFSense_M_MS_TAB.plane_result_val.set("不通过")
            self.TOFSense_M_MS_TAB.plane_result.config(fg="red")
        self.TOFSense_M_MS_TAB.plane_std_val.set(round(plane_std_val, 4))

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
                self.TOFSense_M_MS_TAB.pixels_dis_deque["dis_" + str(i)].append(dis)
                index += 12
            return dis_data


class TOFSENSE_F(Thread):
    def __init__(self, ser, window, data):
        super().__init__()
        self.daemon=True
        self.running = True
        self.ser = ser
        self.TOFSense_F_FP_TAB = window
        self.default_data = data
        self.start()

    def close(self):
        self.running = False
        

    def big_small_end_convert(self, data):
        data = binascii.hexlify(binascii.unhexlify(bytes(data.encode()))[::-1])
        return int(data.decode(), 16)

    def analyse_data(self, data):
        data = "57" + data
        parsed_data = {}
        parsed_data["frame_header"] = data[:2]
        parsed_data["function_mark"] = data[2:4]
        if (
            parsed_data["frame_header"] == _frame_header
            and parsed_data["function_mark"] == _function_mark
        ):
            # parsed_data["reserved"] = data[4:6]
            # parsed_data["id"] = data[6:8]
            # parsed_data["System_time"] = data[8:16]
            parsed_data["dis"] = self.big_small_end_convert(data[16:22]) / 1000
            # parsed_data["dis_status"] = data[22:24]
            # parsed_data["signal_strength"] = data[24:28]
            # parsed_data["range_precision"] = data[28:30]
            # parsed_data["Sum_Check"] = data[30:32]
            self.TOFSense_F_FP_TAB.points_dis_deque.append(parsed_data["dis"])
            return parsed_data["dis"]
        else:
            return 0

    def cal_ptp(self, dis_deque):
        ptp_value = ptp(array(dis_deque))
        if ptp_value <= self.default_data["ptp"]:
            self.TOFSense_F_FP_TAB.ptp_result_val.set("通过")
            self.TOFSense_F_FP_TAB.ptp_result.config(fg="black")
        else:
            self.TOFSense_F_FP_TAB.ptp_result_val.set("不通过")
            self.TOFSense_F_FP_TAB.ptp_result.config(fg="red")
        self.TOFSense_F_FP_TAB.ptp_val.set(round(ptp_value, 4))

    def cal_accrate(self, dis_deque):
        acc_value = max(abs(array(dis_deque) - self.default_data["dis"]))

        if acc_value <= self.default_data["accuracy"]:
            self.TOFSense_F_FP_TAB.accurate_result_val.set("通过")
            self.TOFSense_F_FP_TAB.accurate_result.config(fg="black")
        else:
            self.TOFSense_F_FP_TAB.accurate_result_val.set("不通过")
            self.TOFSense_F_FP_TAB.accurate_result.config(fg="red")
        self.TOFSense_F_FP_TAB.accurate_val.set(round(acc_value, 4))

    def run(self):
        while self.running:
            try:
                header = self.ser.read(1).hex()
                if header == _frame_header:
                    data = self.ser.read(_data_length).hex()
                    dis = self.analyse_data(data.strip())
                    if dis:
                        dis_deque = deepcopy(self.TOFSense_F_FP_TAB.points_dis_deque)
                        self.cal_accrate(dis_deque)
                        self.cal_ptp(dis_deque)
            except SerialException as e:
                self.close()
                log.error(e)
            except Exception as e:
                log.error(e)
