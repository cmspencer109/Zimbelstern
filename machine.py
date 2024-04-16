# machine simulator for running micropython locally


class Pin:
    OUT = "OUT"
    IN = "IN"
    PULL_UP = "PULL_UP"
    pin_val = None

    def __init__(self, pin_number, mode=None, pull=None):
        self.pin_number = pin_number
        self.mode = mode
        self.pull = pull

    def init(self, mode):
        self.mode = mode

    def value(self, val=None):
        if val is not None:
            self.pin_val = val
        return self.pin_val


class UART:
    def __init__(self, uart_number, baudrate, tx=None, rx=None):
        self.uart_number = uart_number
        self.baudrate = baudrate
        self.tx = tx
        self.rx = rx

    def init(self, baudrate, tx=None, rx=None):
        self.baudrate = baudrate
        self.tx = tx
        self.rx = rx

    def write(self, data):
        pass
        # print(f"UART {self.uart_number} writing: {data}")

    def read(self, num_bytes):
        pass
        # print(f"UART {self.uart_number} reading {num_bytes} bytes")

    def readline(self):
        pass
        # print(f"UART {self.uart_number} reading a line")

    def any(self):
        pass
        # print(f"Checking if UART {self.uart_number} has any data available")


class ADC:
    def __init__(self, pin_number):
        self.pin_number = pin_number

    def read_u16(self):
        # Mock the ADC reading
        # pot returns a reading between 0 and 65535
        return 65535
