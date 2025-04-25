nbiot_cmds = [
    ("AT+QSCLK=0\r\n", "OK"),
    ("AT+QIDNSCFG=0,\"8.8.8.8\"\r\n", "OK"),
    ("AT+CCLK?\r\n", "+CCLK:"),
    ("AT+CSQ\r\n", "+CSQ:"),
    # ("AT+QMTOPEN=0,\"137.135.83.217\",1883\r\n", "+QMTOPEN: 0,0"),
    # ("AT+QMTCONN=0,\"pollen-bc660\"\r\n", "+QMTCONN: 0,0"),
    # ("AT+QCFG=\"wakeupRXD\",0\r\n", "OK"),
    # ("AT+QSCLK=1\r\n", "OK"),
]

MQTT_cmds = [
    ("AT+QMTOPEN=0,\"137.135.83.217\",1883", "+QMTOPEN: 0,0"),
    ("AT+QMTCONN=0,\"pollen-bc660\"", "+QMTCONN: 0,0"),
    ("AT+QMTPUB=0,0,0,0,\"/pollen\"", "+QMTPUB: 0,0"),
    ("AT+QMTDISC=0", "+QMTDISC: 0,0"),
]

class MQTT:
    def __init__(self, uart):
        self.uart = uart
        self.mqtt_connected = False
        self.cmd_index = 0
        self.sent_cmd_index = -1
        self.mqtt_cmd_index = 0
        self.mqtt_sent_cmd_index = -1
        self.mqtt_ready_to_send = False
        self.publish_buffer = ""
        self.rx_buffer = bytearray()
        self.RX_BUF_SIZE = 256
        self.on_publish_done = None
        self.callback_func = None
        self.callback_on_resp = ""

    def uart_puts(self, data):
        self.uart.write(data.encode())

    def uart_tx_wait_blocking(self):
        pass  # simulate delay or flush here

    def send_next_cmd(self):
        if self.mqtt_connected:
            return
        if self.cmd_index >= len(nbiot_cmds):
            self.mqtt_connected = True
            if self.on_publish_done:
                self.on_publish_done(True)
            return
        print(f"Sending command: {nbiot_cmds[self.cmd_index][0]}")
        self.uart_puts(nbiot_cmds[self.cmd_index][0])
        self.uart_tx_wait_blocking()
        self.sent_cmd_index = self.cmd_index

    def send_next_mqtt_cmd(self):
        if self.mqtt_cmd_index >= len(MQTT_cmds):
            if self.on_publish_done:
                self.on_publish_done(True)
            return
        cmd = MQTT_cmds[self.mqtt_cmd_index]
        print(f"Sending command: {cmd[0]}")
        self.uart_puts(cmd[0] + "\r\n")
        self.uart_tx_wait_blocking()
        self.mqtt_sent_cmd_index = self.mqtt_cmd_index

    def mqtt_publish_data(self):
        self.uart_puts(self.publish_buffer)
        self.uart_puts("\x1a")
        self.mqtt_ready_to_send = False

    def publish(self, data):
        if self.on_publish_done:
            self.on_publish_done(False)
        self.publish_buffer = data
        self.mqtt_ready_to_send = True
        self.mqtt_cmd_index = 0
        self.send_next_mqtt_cmd()

    def on_receive(self, line):
        print(f"NB-IoT: {line}")

        if line.startswith("ERROR"):
            self.mqtt_connected = False
            self.reset()

        elif line.startswith("+CCLK:"):
            self.set_rtc(line[7:])

        elif line.startswith("+CEREG: 5"):
            self.cmd_index = 0
            self.mqtt_connected = False
            self.send_next_cmd()

        elif not self.mqtt_connected and self.sent_cmd_index > -1 and line.startswith(nbiot_cmds[self.sent_cmd_index][1]):
            self.cmd_index += 1
            self.send_next_cmd()

        elif self.mqtt_sent_cmd_index > -1 and line.startswith(MQTT_cmds[self.mqtt_sent_cmd_index][1]):
            self.mqtt_cmd_index += 1
            self.send_next_mqtt_cmd()

        elif line == ">" and self.mqtt_ready_to_send:
            self.mqtt_publish_data()

        elif self.callback_on_resp and line.startswith(self.callback_on_resp):
            if self.callback_func:
                self.callback_func()
            self.callback_func = None
            self.callback_on_resp = ""

    def on_rx(self):
        while self.uart.any():
            ch = self.uart.read(1)
            if ch in (b'\n', b'\r'):
                if not self.rx_buffer:
                    continue
                line = self.rx_buffer.decode().strip()
                self.rx_buffer = bytearray()
                self.on_receive(line)
                return
            if len(self.rx_buffer) < self.RX_BUF_SIZE - 1:
                self.rx_buffer.extend(ch)

    def reset(self):
        self.uart_puts("AT+QRST=1\r\n")

    def set_rtc(self, datetime):
        t = {
            "year": int(datetime[0:2]),
            "month": int(datetime[3:5]),
            "day": int(datetime[6:8]),
            "dotw": 0,
            "hour": int(datetime[9:11]),
            "min": int(datetime[12:14]),
            "sec": int(datetime[15:17])
        }
        # Placeholder for setting RTC
        print("Set RTC to:", t)

    def cmd(self, cmd, ok_response, cb):
        self.callback_on_resp = ok_response
        self.callback_func = cb
        self.uart_puts(cmd + "\r\n")