import ustruct

class MPU6050:
    def __init__(self, i2c, addr=0x68):
        self.i2c = i2c
        self.addr = addr
        self.buf = bytearray(14)
        try:
            self.i2c.writeto_mem(self.addr, 0x6B, b'\x00')  # Wake up MPU6050
        except OSError as e:
            print("Failed to wake up MPU6050:", e)

    def read_accel_gyro(self):
        try:
            self.i2c.readfrom_mem_into(self.addr, 0x3B, self.buf)
        except OSError as e:
            print("Failed to read data:", e)
            return (0, 0, 0), (0, 0, 0)
        accel = self._convert_data(self.buf[0:6])
        gyro = self._convert_data(self.buf[8:14])
        return accel, gyro

    def _convert_data(self, data):
        return tuple(ustruct.unpack('>hhh', data))

    def get_accel_data(self):
        accel, _ = self.read_accel_gyro()
        return {'x': accel[0] / 16384, 'y': accel[1] / 16384, 'z': accel[2] / 16384}

    def get_gyro_data(self):
        _, gyro = self.read_accel_gyro()
        return {'x': gyro[0] / 131, 'y': gyro[1] / 131, 'z': gyro[2] / 131}
