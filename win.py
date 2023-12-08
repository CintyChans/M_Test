from tkinter import (
    ttk,
    Tk,
    Label,
    Entry,
    Button,
    Frame,
    StringVar,
    IntVar,
    X,
    DoubleVar,
    BOTH,
)
from tkinter.ttk import Notebook
from collections import deque
from env import log, _baudrate, _title, _padx, _pady, _width, _sticky


class Window(Tk):
    def __init__(self):
        super().__init__()
        self.title(_title)
        self.notebook = Notebook(self)
        self.TOFSense_M_MS_TAB = TOFSense_M_MS_Frame(self)
        self.TOFSense_F_FP_TAB = TOFSense_F_FP_Frame(self)
        self.notebook.add(self.TOFSense_M_MS_TAB, text="M/MS")
        self.notebook.add(self.TOFSense_F_FP_TAB, text="F/FP")
        self.notebook.pack(padx=10, pady=5, fill=BOTH, expand=True)


class TOFSense_M_MS_Frame(Frame):
    def __init__(self, master):
        super().__init__(master)
        self.pixels_num = 64
        self.connecting = False
        self.init_val()
        self.set_top_Frame()
        self.set_second_Frame()

    def init_val(self):
        self.baudrateval = IntVar()
        self.deque_size_val = IntVar()
        self.plane_result_val = StringVar()
        self.plane_std_val = DoubleVar()
        self.accuracy_res_val = StringVar()
        self.accuracy_val = DoubleVar()
        self.pixel_alone_std_val = DoubleVar()
        self.pixel_alone_res_val = StringVar()
        self.accuracy_val_2 = DoubleVar()
        self.baudrateval.set(_baudrate)
        self.pixels_dis_deque = {}

    def set_top_Frame(self):
        self.top = Frame(self)
        self.port_btn = Button(self.top, text="扫描串口", bg="white")
        self.port_box = ttk.Combobox(self.top, state="readonly", width=_width)
        self.port_btn.grid(row=0, column=0, sticky=_sticky, pady=_pady, padx=_padx)
        self.port_box.grid(row=0, column=1, sticky=_sticky, pady=_pady, padx=_padx)

        self.baudrate = Entry(self.top, textvariable=self.baudrateval, width=_width)
        baudrate = Label(self.top, text="baudrate:")
        baudrate.grid(row=0, column=2, sticky=_sticky, pady=_pady, padx=_padx)
        self.baudrate.grid(row=0, column=3, sticky=_sticky, pady=_pady, padx=_padx)

        Label(self.top, text="Type:").grid(
            row=0, column=4, sticky=_sticky, pady=_pady, padx=_padx
        )
        self.type = ttk.Combobox(self.top, state="readonly", width=_width)
        self.type["value"] = ["M", "MS"]
        self.type.current(0)
        self.type.grid(row=0, column=5, sticky=_sticky, pady=_pady, padx=_padx)

        self.connect_btn = Button(self.top, text="连接串口", bg="white")
        self.connect_btn.grid(row=0, column=6, sticky=_sticky, pady=_pady, padx=_padx)
        Label(self.top, text="deque size:").grid(
            row=1, column=0, sticky=_sticky, pady=_pady, padx=_padx
        )
        self.deque_size = Entry(self.top, textvariable=self.deque_size_val)
        self.deque_size.bind("<Return>", self.update_deque_size)
        self.deque_size.grid(row=1, column=1, sticky=_sticky, pady=_pady, padx=_padx)
        self.top.pack(expand=1, fill=X)

    def set_second_Frame(self):
        self.second_Frame = Frame(self)
        self.second_Frame.grid_columnconfigure(0, weight=1)
        self.second_Frame.grid_columnconfigure(1, weight=30)
        self.second_Frame.grid_columnconfigure(2, weight=1)
        self.second_Frame.grid_columnconfigure(3, weight=10)
        self.second_Frame.grid_columnconfigure(4, weight=1)
        self.second_Frame.grid_columnconfigure(5, weight=10)
        # [1]

        Label(self.second_Frame, text="平面检测:").grid(row=0, column=0, sticky=_sticky)
        self.plane_result = Label(
            self.second_Frame,
            textvariable=self.plane_result_val,
            font=("黑体", 50),
            width=10,
        )
        Label(self.second_Frame, text="std:", width=15).grid(
            row=0, column=2, sticky="E"
        )
        self.plane_std = Label(
            self.second_Frame, textvariable=self.plane_std_val, width=15
        )
        self.plane_std.grid(row=0, column=3)
        self.plane_result.grid(row=0, column=1)

        # [2]
        Label(self.second_Frame, text="像素点单独标准差检测:").grid(
            row=1, column=0, sticky=_sticky
        )
        self.pixel_alone_result = Label(
            self.second_Frame, textvariable=self.pixel_alone_res_val, font=("黑体", 50)
        )
        self.pixel_alone_result.grid(row=1, column=1)
        Label(self.second_Frame, text="max_std:", width=15).grid(
            row=1, column=2, sticky=_sticky
        )
        self.max_pixel_alone_std = Label(
            self.second_Frame, textvariable=self.pixel_alone_std_val, width=15
        )
        self.max_pixel_alone_std.grid(row=1, column=3)
        # [3]

        Label(self.second_Frame, text="精度检测:").grid(row=2, column=0, sticky=_sticky)
        self.accuracy_result = Label(
            self.second_Frame, textvariable=self.accuracy_res_val, font=("黑体", 50)
        )
        self.accuracy_result.grid(row=2, column=1)
        Label(self.second_Frame, text="center acc :", width=15).grid(
            row=2, column=2, sticky=_sticky
        )
        self.max_accuracy_1 = Label(
            self.second_Frame, textvariable=self.accuracy_val, width=15
        )
        self.max_accuracy_1.grid(row=2, column=3)
        Label(self.second_Frame, text="other acc :", width=15).grid(
            row=2, column=4, sticky="E"
        )
        self.max_accuracy_2 = Label(
            self.second_Frame, textvariable=self.accuracy_val_2, width=15
        )
        self.max_accuracy_2.grid(row=2, column=5)
        self.second_Frame.pack(expand=1, fill=X)

    def update_deque_size(self, event):
        if self.pixels_dis_deque:
            for i in range(self.pixels_num):
                self.pixels_dis_deque["dis_" + str(i)] = deque(
                    self.pixels_dis_deque["dis_" + str(i)],
                    maxlen=self.deque_size_val.get(),
                )
            log.info(f"update_deque_size = {self.deque_size_val.get()}")

    def init_deque(self):
        for i in range(self.pixels_num):
            self.pixels_dis_deque["dis_" + str(i)] = deque(
                maxlen=self.deque_size_val.get()
            )
        log.info(f"init_deque_size = {self.deque_size_val.get()}")


class TOFSense_F_FP_Frame(Frame):
    def __init__(self, master):
        super().__init__(master)
        self.connecting = False
        self.init_val()
        self.set_top_Frame()
        self.set_second_Frame()

    def init_val(self):
        self.points_dis_deque = deque()
        self.baudrateval = IntVar()
        self.deque_size_val = IntVar()
        self.accurate_result_val = StringVar()
        self.accurate_val = DoubleVar()
        self.ptp_result_val = StringVar()
        self.ptp_val = DoubleVar()
        self.baudrateval.set(_baudrate)

    def set_top_Frame(self):
        self.top = Frame(self)
        self.port_btn = Button(self.top, text="扫描串口", bg="white")
        self.port_box = ttk.Combobox(self.top, state="readonly", width=_width)
        self.port_btn.grid(row=0, column=0, sticky=_sticky, pady=_pady, padx=_padx)
        self.port_box.grid(row=0, column=1, sticky=_sticky, pady=_pady, padx=_padx)
        self.baudrate = Entry(self.top, textvariable=self.baudrateval, width=_width)
        baudrate = Label(self.top, text="baudrate:")
        baudrate.grid(row=0, column=2, sticky=_sticky, pady=_pady, padx=_padx)
        self.baudrate.grid(row=0, column=3, sticky=_sticky, pady=_pady, padx=_padx)

        Label(self.top, text="Type:").grid(
            row=0, column=4, sticky=_sticky, pady=_pady, padx=_padx
        )
        self.type = ttk.Combobox(self.top, state="readonly", width=_width)
        self.type["value"] = ["F", "FP"]
        self.type.current(0)
        self.type.grid(row=0, column=5, sticky=_sticky, pady=_pady, padx=_padx)

        self.connect_btn = Button(self.top, text="连接串口", bg="white")
        self.connect_btn.grid(row=0, column=6, sticky=_sticky, pady=_pady, padx=_padx)
        Label(self.top, text="deque size:").grid(
            row=1, column=0, sticky=_sticky, pady=_pady, padx=_padx
        )

        self.deque_size = Entry(self.top, textvariable=self.deque_size_val)
        self.deque_size.bind("<Return>", self.update_deque_size)
        self.deque_size.grid(row=1, column=1, sticky=_sticky, pady=_pady, padx=_padx)
        self.top.pack(expand=1, fill=X)

    def set_second_Frame(self):
        self.second_Frame = Frame(self)
        # [1]

        Label(self.second_Frame, text="精度检测:").grid(row=0, column=0, sticky=_sticky)
        self.accurate_result = Label(
            self.second_Frame,
            textvariable=self.accurate_result_val,
            font=("黑体", 50),
            width=10,
        )
        Label(self.second_Frame, text="accurate:", width=15).grid(
            row=0, column=2, sticky="E"
        )
        self.accurate = Label(
            self.second_Frame, textvariable=self.accurate_val, width=15
        )
        self.accurate_result.grid(row=0, column=1)
        self.accurate.grid(row=0, column=3)
        self.second_Frame.pack(expand=1, fill=X)

        # [2]
        Label(self.second_Frame, text="波动检测:").grid(row=1, column=0, sticky=_sticky)
        self.ptp_result = Label(
            self.second_Frame,
            textvariable=self.ptp_result_val,
            font=("黑体", 50),
            width=10,
        )
        Label(self.second_Frame, text="ptp:", width=15).grid(
            row=1, column=2, sticky="E"
        )
        self.ptp = Label(self.second_Frame, textvariable=self.ptp_val, width=15)
        self.ptp_result.grid(row=1, column=1)
        self.ptp.grid(row=1, column=3)

        self.second_Frame.pack(expand=1, fill=X)

    def update_deque_size(self, event):
        if self.points_dis_deque:
            self.points_dis_deque = deque(
                self.points_dis_deque,
                maxlen=self.deque_size_val.get(),
            )
        log.info(f"update_deque_size = {self.deque_size_val.get()}")

    def init_deque(self):
        self.points_dis_deque = deque(maxlen=self.deque_size_val.get())
        log.info(f"init_deque_size = {self.deque_size_val.get()}")

