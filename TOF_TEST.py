from win import *
import serial
import serial.tools.list_ports
from env import default_data
from TOFSense import TOFSENSE_F, TOFSENSE_M
import time
from threading import *


class MainServer:
    def __init__(self):
        self.window = Window()
        self.TOFSense_M_MS_TAB = self.window.TOFSense_M_MS_TAB
        self.TOFSense_F_FP_TAB = self.window.TOFSense_F_FP_TAB
        self.TOFSense_M_MS_TAB.port_btn.bind("<Button-1>", self.scan_port_M)
        self.TOFSense_F_FP_TAB.port_btn.bind("<Button-1>", self.scan_port_F)
        self.TOFSense_M_MS_TAB.connect_btn.bind("<Button-1>", self.connect_port_M)
        self.TOFSense_F_FP_TAB.connect_btn.bind("<Button-1>", self.connect_port_F)
        self.window.protocol("WM_DELETE_WINDOW", self.close)
        self.TOFSense_M_MS_TAB.deque_size_val.set(
            default_data["M"]["default_deque_size"]
        )
        self.TOFSense_F_FP_TAB.deque_size_val.set(
            default_data["F"]["default_deque_size"]
        )
        self.window.mainloop()

    def scan_port_M(self, e):
        port_list = list(serial.tools.list_ports.comports())
        port = [i[0] for i in port_list]
        try:
            self.TOFSense_M_MS_TAB.port_box["value"] = port
            self.TOFSense_M_MS_TAB.port_box.current(0)
        except Exception as e:
            log.error(e)
            self.TOFSense_M_MS_TAB.port_box["value"] = [""]
            self.TOFSense_M_MS_TAB.port_box.current(0)

    def scan_port_F(self, e):
        port_list = list(serial.tools.list_ports.comports())
        port = [i[0] for i in port_list]
        try:
            self.TOFSense_F_FP_TAB.port_box["value"] = port
            self.TOFSense_F_FP_TAB.port_box.current(0)
        except Exception as e:
            log.error(e)
            self.TOFSense_F_FP_TAB.port_box["value"] = [""]
            self.TOFSense_F_FP_TAB.port_box.current(0)

    def timer(self, flag):
        try:
            while self.program.running:
                time.sleep(1)
            if self.port.is_open:
                self.port.close()
            if flag == "F":
                self.TOFSense_F_FP_TAB.connecting = False
                self.TOFSense_F_FP_TAB.connect_btn.config(bg="white", text="连接串口")
            else:
                self.TOFSense_M_MS_TAB.connecting = False
                self.TOFSense_M_MS_TAB.connect_btn.config(bg="#75bbfd", text="关闭串口")
        except Exception as e:
            log.error(e)

    def connect_port_M(self, e):
        data = {}
        try:
            if not self.TOFSense_M_MS_TAB.connecting:
                if self.TOFSense_M_MS_TAB.type.get() == "M":
                    data = default_data["M"]
                else:
                    data = default_data["MS"]
                self.port = serial.Serial(
                    self.TOFSense_M_MS_TAB.port_box.get(),
                    self.TOFSense_M_MS_TAB.baudrateval.get(),
                )
                self.TOFSense_M_MS_TAB.connecting = True
                self.TOFSense_M_MS_TAB.init_deque()
                self.program = TOFSENSE_M(self.port, self.TOFSense_M_MS_TAB, data)
                self.TOFSense_M_MS_TAB.connect_btn.config(bg="#75bbfd", text="关闭串口")
                log.info(f"type={self.TOFSense_M_MS_TAB.type.get()},params={data}")
                Thread(target=self.timer, args="M",daemon=True).start()
            else:
                self.TOFSense_M_MS_TAB.connecting = False
                self.program.close()
                self.port.close()
                self.TOFSense_M_MS_TAB.connect_btn.config(bg="white", text="连接串口")
        except Exception as e:
            log.error(e)

    def connect_port_F(self, e):
        data = {}
        try:
            if not self.TOFSense_F_FP_TAB.connecting:
                if self.TOFSense_F_FP_TAB.type.get() == "F":
                    data = default_data["F"]
                else:
                    data = default_data["FP"]
                self.port = serial.Serial(
                    self.TOFSense_F_FP_TAB.port_box.get(),
                    self.TOFSense_F_FP_TAB.baudrateval.get(),
                )
                self.TOFSense_F_FP_TAB.connecting = True
                self.TOFSense_F_FP_TAB.init_deque()
                self.program = TOFSENSE_F(self.port, self.TOFSense_F_FP_TAB, data)
                self.TOFSense_F_FP_TAB.connect_btn.config(bg="#75bbfd", text="关闭串口")
                log.info(f"type={self.TOFSense_F_FP_TAB.type.get()},params={data}")
                Thread(target=self.timer, args="F", daemon=True).start()
            else:
                self.TOFSense_F_FP_TAB.connecting = False
                self.program.close()
                self.port.close()
                self.TOFSense_F_FP_TAB.connect_btn.config(bg="white", text="连接串口")
        except Exception as e:
            log.error(e)

    def close(self):
        try:
            self.program.close()
            self.port.close()
            log.close()
            self.window.destroy()
        except Exception as e:
            log.error(2)



server = MainServer()
