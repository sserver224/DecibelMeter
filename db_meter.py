import os, errno
import pyaudio
from scipy.signal import lfilter
import numpy
from tkinter import *
from threading import Thread
from tk_tools import *
from customtkinter import *
import time
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)
from tkinter import messagebox
import sys
from idlelib.tooltip import Hovertip
set_appearance_mode("System")  # Modes: system (default), light, dark
set_default_color_theme("blue")
try:
    from winreg import *
except:
    reg_present=False
    messagebox.askokcancel('Limited Features', "Registry not present. Dosimeter disabled. OK to continue, Cancel to quit.", icon='warning')
else:
    reg_present=True
def get_resource_path(relative_path):
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)
def toggle_dosi():
    global dosi_enabled
    dosi_enabled=enable_dosi.get()
def reset():
    global start, dosimeter_times, runTime, x, y, plot1
    dosimeter_times={'82dB':0, '85dB':0, '88dB':0, '91dB':0, '94dB':0, '97dB':0, '100dB':0, '103dB':0, '106dB':0, '109dB':0, '112dB':0, '115dB':0, '118dB':0}
    x=[]
    y=[]
    runTime=0
win=CTk()
win.title('Decibel Meter v1.2 (c) sserver')
win.grid()
win.resizable(False, False)
if reg_present:
    CreateKeyEx(OpenKey(HKEY_CURRENT_USER, 'Software', reserved=0, access=KEY_ALL_ACCESS), 'sserver\Decibel Meter', reserved=0)
    try:
        dosi_enabled=bool(QueryValueEx(OpenKey(OpenKey(OpenKey(HKEY_CURRENT_USER, 'Software', reserved=0, access=KEY_ALL_ACCESS), 'sserver', reserved=0, access=KEY_ALL_ACCESS), 'Decibel Meter', reserved=0, access=KEY_ALL_ACCESS), 'DosimeterEnabled')[0])
    except OSError:
        SetValueEx(OpenKey(OpenKey(OpenKey(HKEY_CURRENT_USER, 'Software', reserved=0, access=KEY_ALL_ACCESS), 'sserver', reserved=0, access=KEY_ALL_ACCESS), 'Decibel Meter', reserved=0, access=KEY_ALL_ACCESS), 'DosimeterEnabled', 0, REG_DWORD, 0)
        dosi_enabled=False
        messagebox.showwarning('Registry Error', 'Error reading settings. Resetting to default...')
else:
    dosi_enabled=False
dosi_enabled_first=dosi_enabled
runTime=0
measure=False
recording=False
start=time.time()
tabview =CTkTabview(win)
tabview.pack(padx=20, pady=20)
tabview.add("Meter")  # add tab at the end
tabview.add("Dosimeter")
tabview.add("Recording")
root=tabview.tab("Meter")
sub=tabview.tab("Dosimeter")
sub1=tabview.tab("Recording")
led = Led(root, size=20)
led.grid(column=2, row=14)
Hovertip(led,'1 dB\nAll is OK\nThreshold of hearing')
gaugedb=SevenSegmentDigits(root, digits=3, digit_color='#00ff00', background='black')
gaugedb.grid(column=1, row=1)
dosidb=SevenSegmentDigits(sub, digits=3, digit_color='#00ff00', background='black')
dosidb.grid(column=1, row=2)
graphdb=SevenSegmentDigits(sub1, digits=3, digit_color='#00ff00', background='black')
graphdb.grid(column=1, row=2)
Hovertip(gaugedb,"Current dBA level")
led0 = Led(root, size=20)
led0.grid(column=2, row=13)
Hovertip(led0,'10 dB\nAll is OK\nEquivalent to rustling leaves in the distance')
led1 = Led(root, size=20)
led1.grid(column=2, row=12)
Hovertip(led1,'20 dB\nAll is OK\nEquivalent to a background in a movie studio')
led2 = Led(root, size=20)
led2.grid(column=2, row=11)
Hovertip(led2,'30 dB\nAll is OK\nEquivalent to a quiet bedroom')
led3 = Led(root, size=20)
led3.grid(column=2, row=10)
Hovertip(led3,'40 dB\nAll is OK\nEquivalent to a whisper')
led4 = Led(root, size=20)
led4.grid(column=2, row=9)
Hovertip(led4,'50 dB\nAll is OK\nEquivalent to a quiet home')
led5 = Led(root, size=20)
led5.grid(column=2, row=8)
Hovertip(led5,'60 dB\nAll is OK\nEquivalent to a quiet street')
led6 = Led(root, size=20)
led6.grid(column=2, row=7)
Hovertip(led6,'70 dB\nAll is OK\nEquivalent to a normal conversation')
led7 = Led(root, size=20)
led7.grid(column=2, row=6)
Hovertip(led7,'80 dB\nA little loud, may cause hearing damage in sensitive people.\nEquivalent to loud singing')
led8 = Led(root, size=20)
led8.grid(column=2, row=5)
Hovertip(led8,'90 dB\nLoud; repeated and/or long term exposure at this level may damage hearing.\nEquivalent to a motorcycle')
led9 = Led(root, size=20)
led9.grid(column=2, row=4)
Hovertip(led9,'100 dB\nCritically loud, even short exposure to this level can damage hearing.\nEquivalent to a subway')
led10 = Led(root, size=20)
led10.grid(column=2, row=3)
Hovertip(led10,'110 dB\nDangerous, even short exposure to this level can damage hearing.\nEquivalent to a helicopter overheaad')
led11 = Led(root, size=20)
led11.grid(column=2, row=2)
win.iconbitmap(get_resource_path('snd.ico'))
Hovertip(led11,"120 dB\nDangerous, even short exposure to this level can damage hearing.\nYou might feel pain at this level.\nEquivalent to a rock concert")
CTkLabel(sub, text='Instantaneous dBA level').grid(column=1, row=1)
CTkLabel(sub1, text='Instantaneous dBA level').grid(column=1, row=1)
db_levels=[82, 85, 88, 91, 94, 97, 100, 103, 106, 109, 112, 115, 118]
niosh_limits=[57600, 28800, 14400, 7200, 3600, 1800, 900, 450, 225, 120, 60, 30, 15]
db_levels.reverse()
niosh_limits.reverse()
enable_dosi=CTkSwitch(sub, text='Enable Dosimeter (restart app to apply)', command=toggle_dosi)
enable_dosi.grid(column=1, row=3)
def record_frame():
    global recording, rec_start, db, f
    time_trunc='%.1f' % (time.time()-rec_start)
    f.write(time_trunc+','+str(int(db))+'\n')
    if recording:
        win.after(500, record_frame)
    else:
        f.close()
def record():
    global recording, f, rec_start
    if not recording:
        rec.configure(text='Stop')
        rec_start=time.time()
        recording=True
        f=open(os.getenv('HOMEPATH')+'\\Music\\mic_levels.csv', 'w')
        f.write('Seconds,Decibels\n')
        record_frame()
    else:
        recording=False
        rec.configure(text='Record')
if not reg_present:
    enable_dosi.configure(state=DISABLED)
if dosi_enabled:
    enable_dosi.select()
    doseLabel=CTkLabel(sub, text=r'Dose: 0.0%', width=40)
    doseLabel.grid(column=1, row=4)
    dosebar=CTkProgressBar(sub, mode='determinate')
    dosebar.grid(column=2, row=4)
    timeLabel=CTkLabel(sub, text='0 sec', width=30)
    timeLabel.grid(column=2, row=2)
    pdose=CTkLabel(sub, text='Projected dose: 0 sec', width=40)
    CTkButton(sub, text='Reset', command=reset).grid(column=2, row=3)
    CTkLabel(sub1, text='Recording to Music\\mic_levels.csv.\nMake sure the file does not exist, or it will be overwritten.').grid(column=1, row=3)
    rec=CTkButton(sub1, text='Record', command=record)
    rec.grid(column=1, row=4)
    for i in range(len(db_levels)):
        db_level=db_levels[i]
        exec("label_"+str(db_level)+"=CTkLabel(sub, width=40, text='"+str(db_level)+"dBA: 0/"+str(niosh_limits[i])+" sec')")
        exec("label_"+str(db_level)+".grid(column=1, row="+str(i+5)+")")
        exec("bar_"+str(db_level)+'=CTkProgressBar(sub, mode="determinate")')
        exec("bar_"+str(db_level)+'.grid(column=2, row='+str(i+5)+')')
else:
    CTkLabel(sub, text='Dosimeter is not enabled', width=60).grid(column=1, row=4)
    CTkLabel(sub1, text='Dosimeter must be enabled', width=60).grid(column=1, row=4)    
CTkLabel(root, text='120').grid(column=1, row=2)
CTkLabel(root, text='100').grid(column=1, row=4)
CTkLabel(root, text='Danger').grid(column=3, row=4)
CTkLabel(root, text='80').grid(column=1, row=6)
CTkLabel(root, text='Loud').grid(column=3, row=6)
CTkLabel(root, text='60').grid(column=1, row=8)
CTkLabel(root, text='40').grid(column=1, row=10)
CTkLabel(root, text='20').grid(column=1, row=12)
CTkLabel(root, text='dB').grid(column=1, row=14)
CTkLabel(root, text='OK').grid(column=3, row=14)
CTkLabel(root, text='Max').grid(column=3, row=0)
CTkLabel(root, text='dBA').grid(column=1, row=0)
CTkLabel(root, text='-').grid(column=1, row=3)
CTkLabel(root, text='-').grid(column=1, row=5)
CTkLabel(root, text='-').grid(column=1, row=7)
CTkLabel(root, text='-').grid(column=1, row=9)
CTkLabel(root, text='-').grid(column=1, row=11)
CTkLabel(root, text='-').grid(column=1, row=13)
CTkLabel(root, text='dB Offset').grid(column=2, row=0)
maxdb_display=SevenSegmentDigits(root, digits=3, digit_color='#00ff00', background='black')
maxdb_display.grid(column=3, row=1)
dosimeter_times={'82dB':0, '85dB':0, '88dB':0, '91dB':0, '94dB':0, '97dB':0, '100dB':0, '103dB':0, '106dB':0, '109dB':0, '112dB':0, '115dB':0, '118dB':0}
Hovertip(maxdb_display,"Max dBA level since program start")
CHUNKS = [4096, 9600]
win.geometry('502x586')
CHUNK = CHUNKS[1]
FORMAT = pyaudio.paInt16
CHANNEL = 1 
RATES = [44300, 48000]
RATE = RATES[1]
offset=StringVar()
offset.set('0')
spinbox=CTkOptionMenu(root, variable=offset, width=100, values=tuple(reversed(['-20','-19', '-18', '-17', '-16', '-15', '-14', '-13', '-12', '-11', '-10', '-9', '-8', '-7', '-6', '-5', '-4', '-3', '-2', '-1', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13', '14', '15', '16', '17', '18', '19', '20'])), state='readonly')
spinbox.grid(column=2, row=1)
Hovertip(spinbox,"dB offset (Calibration)\nUse this if the meter is not accurate.\nUse a reliable reference meter (such as a dedicated SPL meter).")
appclosed=False
from scipy.signal import bilinear
start_check=time.time()
db=0
x=[]
y=[]
def timer_dosi():
    global runTime, y, x, start_check
    runTime+=time.time()-start_check
    if db>=82 and db<85:
        dosimeter_times['82dB']+=time.time()-start_check
    if db>=85 and db<88:
        dosimeter_times['85dB']+=time.time()-start_check
    if db>=88 and db<91:
        dosimeter_times['88dB']+=time.time()-start_check
    if db>=91 and db<94:
        dosimeter_times['91dB']+=time.time()-start_check
    if db>=94 and db<97:
        dosimeter_times['94dB']+=time.time()-start_check
    if db>=97 and db<100:
        dosimeter_times['97dB']+=time.time()-start_check
    if db>=100 and db<103:
        dosimeter_times['100dB']+=time.time()-start_check
    if db>=103 and db<106:
        dosimeter_times['103dB']+=time.time()-start_check
    if db>=106 and db<109:
        dosimeter_times['106dB']+=time.time()-start_check
    if db>=109 and db<112:
        dosimeter_times['109dB']+=time.time()-start_check
    if db>=112 and db<115:
        dosimeter_times['112dB']+=time.time()-start_check
    if db>=115 and db<118:
        dosimeter_times['115dB']+=time.time()-start_check
    if db>=118:
        dosimeter_times['118dB']+=time.time()-start_check
    start_check=time.time()
    win.after(200, timer_dosi)
def close():
    global appclosed
    win.destroy()
    if dosi_enabled:
        SetValueEx(OpenKey(OpenKey(OpenKey(HKEY_CURRENT_USER, 'Software', reserved=0, access=KEY_ALL_ACCESS), 'sserver', reserved=0, access=KEY_ALL_ACCESS), 'Decibel Meter', reserved=0, access=KEY_ALL_ACCESS), 'DosimeterEnabled', 0, REG_DWORD, 1)
    else:
        SetValueEx(OpenKey(OpenKey(OpenKey(HKEY_CURRENT_USER, 'Software', reserved=0, access=KEY_ALL_ACCESS), 'sserver', reserved=0, access=KEY_ALL_ACCESS), 'Decibel Meter', reserved=0, access=KEY_ALL_ACCESS), 'DosimeterEnabled', 0, REG_DWORD, 0)
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
def returnSum(myDict):
    mylist = []
    for i in myDict:
        mylist.append(myDict[i])
    final = sum(mylist)
    return final
def listen(old=0, error_count=0, min_decibel=100):
    global appclosed
    global max_decibel
    global measure
    global db
    global start
    if not appclosed:
        try:
            try:
                block = stream.read(CHUNK)
            except IOError as e:
                if not appclosed:
                    error_count += 1
                    messagebox.showerror("Error, ", " (%d) Error recording: %s" % (error_count, e))
            else:
                decoded_block = numpy.frombuffer(block, numpy.int16)
                y = lfilter(NUMERATOR, DENOMINATOR, decoded_block)
                new_decibel = 20*numpy.log10(rms_flat(y))+int(offset.get())
                if runTime>0:
                    runt=runTime
                else:
                    runt=0.1
                if new_decibel<0:
                    new_decibel=0
                old = new_decibel
                db=new_decibel
                gaugedb.set_value(str(int(float('{:.2f}'.format(new_decibel)))))
                dosidb.set_value(str(int(float('{:.2f}'.format(new_decibel)))))
                graphdb.set_value(str(int(float('{:.2f}'.format(new_decibel)))))
                if new_decibel>max_decibel:
                    max_decibel=new_decibel
                if int(db)>0:
                    led.to_green(on=True)
                else:
                    led.to_grey(on=True)
                maxdb_display.set_value(str(int(float(str(max_decibel)))))
                for i in range(0, 12):
                    if int(new_decibel)>=(10*(i+1)):
                        if i>=9:
                            exec("led"+str(i)+".to_red(on=True)")
                        elif i>=7:
                            exec("led"+str(i)+".to_yellow(on=True)")
                        else:
                            exec("led"+str(i)+".to_green(on=True)")
                    else:
                        exec("led"+str(i)+".to_grey(on=True)")
            if dosi_enabled_first:
                dosebar.set(returnSum(dosimeter_times)/runt)
                pdose.configure(text='Projected dose: '+str(int((returnSum(dosimeter_times)*8)/runt))+' sec')
                timeLabel.configure(text=str(int(runt))+' sec')
                doseLabel.configure(text='Dose: '+str(round(returnSum(dosimeter_times)/runt*1000)/10)+'%')
                for i in range(len(db_levels)):
                    db_level=db_levels[i]
                    exec("label_"+str(db_level)+".configure(text='"+str(db_level)+"dBA: "+str(int(dosimeter_times[str(db_level)+'dB']))+'/'+str(niosh_limits[i])+" sec')")
                    exec("bar_"+str(db_level)+".set("+str((dosimeter_times[str(db_level)+'dB']/niosh_limits[i]))+')')
            win.after(20, listen)
        except TclError:
            pass
win.protocol('WM_DELETE_WINDOW', close)
if __name__ == '__main__':
    if dosi_enabled:
        timer_dosi()
    listen()
    win.mainloop()
