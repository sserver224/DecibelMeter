import os, errno
import pyaudio
from scipy.signal import lfilter
import numpy
from tkinter import *
from threading import Thread
from tkinter.ttk import *
from tk_tools import *
from tkinter import messagebox
from idlelib.tooltip import Hovertip
def get_resource_path(relative_path):
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)
root=Tk()
root.title('Decibel Meter v1.0 (c) sserver')
root.grid()
root.resizable(False, False)
gaugedb=SevenSegmentDigits(root, digits=3, digit_color='#00ff00', background='black')
gaugedb.grid(column=1, row=1)
led0 = Led(root, size=20)
led0.grid(column=2, row=13)
led0.to_green(on=False)
Hovertip(led0,'10 dB\nAll is OK')
led1 = Led(root, size=20)
led1.grid(column=2, row=12)
led1.to_green(on=False)
Hovertip(led1,'20 dB\nAll is OK')
led2 = Led(root, size=20)
led2.grid(column=2, row=11)
led2.to_green(on=False)
Hovertip(led2,'30 dB\nAll is OK')
led3 = Led(root, size=20)
led3.grid(column=2, row=10)
led3.to_green(on=False)
Hovertip(led3,'40 dB\nAll is OK')
led4 = Led(root, size=20)
led4.grid(column=2, row=9)
led4.to_green(on=False)
Hovertip(led4,'50 dB\nAll is OK')
led5 = Led(root, size=20)
led5.grid(column=2, row=8)
led5.to_green(on=False)
Hovertip(led5,'60 dB\nAll is OK')
led6 = Led(root, size=20)
led6.grid(column=2, row=7)
led6.to_green(on=False)
Hovertip(led6,'70 dB\nAll is OK')
led7 = Led(root, size=20)
led7.grid(column=2, row=6)
led7.to_yellow(on=False)
Hovertip(led7,'80 dB\nA little loud, may cause hearing damage in sensitive people.')
led8 = Led(root, size=20)
led8.grid(column=2, row=5)
led8.to_yellow(on=False)
Hovertip(led8,'90 dB\nLoud; repeated and/or long term exposure to this level may damage hearing.')
led9 = Led(root, size=20)
led9.grid(column=2, row=4)
led9.to_red(on=False)
Hovertip(led9,'100 dB\nDangerous, even short exposure to this level can damage hearing.')
led10 = Led(root, size=20)
led10.grid(column=2, row=3)
led10.to_red(on=False)
Hovertip(led10,'110 dB\nDangerous, even short exposure to this level can damage hearing.')
led11 = Led(root, size=20)
led11.grid(column=2, row=2)
led11.to_red(on=False)
root.iconbitmap(get_resource_path('snd.ico'))
Hovertip(led11,"120 dB\nDangerous, even short exposure to this level can damage hearing.\nYou might feel pain at this level.")
Label(root, text='120').grid(column=1, row=2)
Label(root, text='100').grid(column=1, row=4)
Label(root, text='Danger').grid(column=3, row=4)
Label(root, text='80').grid(column=1, row=6)
Label(root, text='Loud').grid(column=3, row=6)
Label(root, text='60').grid(column=1, row=8)
Label(root, text='40').grid(column=1, row=10)
Label(root, text='20').grid(column=1, row=12)
Label(root, text='dBA').grid(column=3, row=13)
Label(root, text='Max').grid(column=3, row=0)
Label(root, text='dBA').grid(column=1, row=0)
Label(root, text='dB Offset').grid(column=2, row=0)
maxdb_display=SevenSegmentDigits(root, digits=3, digit_color='#00ff00', background='black')
maxdb_display.grid(column=3, row=1)
CHUNKS = [4096, 9600]
CHUNK = CHUNKS[1]
FORMAT = pyaudio.paInt16
CHANNEL = 1 
RATES = [44300, 48000]
RATE = RATES[1]
offset=StringVar()
offset.set('0')
spinbox=Spinbox(root, from_=-20, to=20, textvariable=offset, state='readonly', width=5)
spinbox.grid(column=2, row=1)
appclosed=False
from scipy.signal import bilinear
def close():
    global appclosed
    root.destroy()
    appclosed=True
    stream.stop_stream()
    stream.close()
    pa.terminate()
def A_weighting(fs):
    f1 = 20.598997
    f2 = 107.65265
    f3 = 737.86223
    f4 = 12194.217
    A1000 = 1.9997

    NUMs = [(2*numpy.pi * f4)**2 * (10**(A1000/20)), 0, 0, 0, 0]
    DENs = numpy.polymul([1, 4*numpy.pi * f4, (2*numpy.pi * f4)**2],
                   [1, 4*numpy.pi * f1, (2*numpy.pi * f1)**2])
    DENs = numpy.polymul(numpy.polymul(DENs, [1, 2*numpy.pi * f3]),
                                 [1, 2*numpy.pi * f2])
    return bilinear(NUMs, DENs, fs)
NUMERATOR, DENOMINATOR = A_weighting(RATE)
def rms_flat(a):
    return numpy.sqrt(numpy.mean(numpy.absolute(a)**2))
pa = pyaudio.PyAudio()
stream = pa.open(format = FORMAT,
                channels = CHANNEL,
                rate = RATE,
                input = True,
                frames_per_buffer = CHUNK)
max_decibel=0
def listen(old=0, error_count=0, min_decibel=100):
    global appclosed
    global max_decibel
    if not appclosed:
        try:
            try:
                block = stream.read(CHUNK)
            except IOError as e:
                if not appclosed:
                    error_count += 1
                    messagebox.showerror("Error, ", " (%d) Error recording: %s" % (error_count, e))
            else:
                decoded_block = numpy.fromstring(block, numpy.int16)
                y = lfilter(NUMERATOR, DENOMINATOR, decoded_block)
                new_decibel = 20*numpy.log10(rms_flat(y))+int(offset.get())
                if new_decibel<0:
                    new_decibel=0
                old = new_decibel
                gaugedb.set_value(str(int(float('{:.2f}'.format(new_decibel)))))
                if new_decibel>max_decibel:
                    max_decibel=new_decibel
                maxdb_display.set_value(str(int(float(str(max_decibel)))))
                for i in range(0, 7):
                    exec("led"+str(i)+".to_green(on=(new_decibel>="+str(10*(i+1))+"))")
                for i in range(7, 9):
                    exec("led"+str(i)+".to_yellow(on=(new_decibel>="+str(10*(i+1))+"))")
                for i in range(9, 12):
                    exec("led"+str(i)+".to_red(on=(new_decibel>="+str(10*(i+1))+"))")
            root.after(50, listen)
        except TclError:
            pass
root.protocol('WM_DELETE_WINDOW', close)
if __name__ == '__main__':
    listen()
    root.mainloop()
