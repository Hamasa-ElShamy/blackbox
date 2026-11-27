import struct, random
random.seed(1)
def sensor():
    t=1700000000; rec=[]
    for i in range(300):
        t+=60; rec.append(struct.pack("<IffHBx8s",t,20+random.random()*5,40+random.random()*20,random.choice([3,7,12]),random.choice([0,1,4]),b"room%d"%random.randint(1,3)))
    return b"SNS1"+b"".join(rec)
def gps():
    # big endian, no header: float64 lat, float64 lon, uint16 speed, uint16 heading
    rec=[]; lat,lon=30.0,31.0
    for i in range(500):
        lat+=random.random()*1e-3; lon+=random.random()*1e-3
        rec.append(struct.pack(">ddHH",lat,lon,random.randint(0,120),random.randint(0,359)))
    return b"".join(rec)
if __name__=="__main__":
    open('sensor.bin','wb').write(sensor()); open('gps.bin','wb').write(gps())
