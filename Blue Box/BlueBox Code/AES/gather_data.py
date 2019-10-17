#!/usr/bin/python3
"""This submodule is used to gather data from a Bluebox device.
The primary function in this module is also called gather_data.

"""

import numpy as np
import struct
import socket
import json
import os
import binascii
import argparse
import datetime
import time
import soundfile
import subprocess
import tempfile
from os.path import expanduser
from mutagen.flac import FLAC
from Crypto.Cipher import AES #pip install pycryptodome

home = expanduser("~")
___default_title___ = "Unknown dataset"
___default_num_seconds___ = 1.0
___default_directory___ = "untracked_data"
___default_calibration___ = os.path.join(home,"Documents/BlueBox/bluebox/device_calibration.json")
___grab_length___ = 16


key= b'\x2b\x7e\x15\x16\x28\xae\xd2\xa6\xab\xf7\x15\x88\x09\xcf\x4f\x3c';

# -----------------------------------------------------------------------
# update_data function
#------------------------------------------------------------------------

def AESDecrypt(ciphertext, key, iv):
    cipher = AES.new(key, AES.MODE_CBC, iv)
    return cipher.decrypt(ciphertext)

def update_data(sock,data_file,live=False,devices={}):
    """Gather a segment of data from a bluebox
    
    """
    
    #Get the latest data from the devices
    try:
        enc_data, addr = sock.recvfrom(144) # buffer size is 144 bytes
        iv = enc_data[128:144]
        data = AESDecrypt(enc_data[:128], key, iv)

    except Exception as e:
        return 0

    if live:
        #Assuming we are only going to use live mode with relatively slow
        #sample rates, let's translate the binary data into readable text
        s = binascii.hexlify(data[0:6]).decode('ascii')
        mac_address = ':'.join(a+b for a,b in zip(s[::2], s[1::2]))
        if mac_address not in devices:
            devices[mac_address] = {}
            devices[mac_address]['x_scale'] = {"12.5":256,"25.0":256,"50.0":256,"100.0":256,"200.0":256,"400.0":256,"800.0":256,"1600.0":256,"3200.0":256}
            devices[mac_address]['y_scale'] = {"12.5":256,"25.0":256,"50.0":256,"100.0":256,"200.0":256,"400.0":256,"800.0":256,"1600.0":256,"3200.0":256}
            devices[mac_address]['z_scale'] = {"12.5":256,"25.0":256,"50.0":256,"100.0":256,"200.0":256,"400.0":256,"800.0":256,"1600.0":256,"3200.0":256}
            devices[mac_address]['x_offset'] = {"12.5":0,"25.0":0,"50.0":0,"100.0":0,"200.0":0,"400.0":0,"800.0":0,"1600.0":0,"3200.0":0}
            devices[mac_address]['y_offset'] = {"12.5":0,"25.0":0,"50.0":0,"100.0":0,"200.0":0,"400.0":0,"800.0":0,"1600.0":0,"3200.0":0}
            devices[mac_address]['z_offset'] = {"12.5":0,"25.0":0,"50.0":0,"100.0":0,"200.0":0,"400.0":0,"800.0":0,"1600.0":0,"3200.0":0}
            devices[mac_address]['id'] = 50 + len(devices)
        if not 'ntp_timestamp' in devices[mac_address]:            
            ntp_timestamp = int.from_bytes(data[6:10], byteorder='little')
            ntp_timestamp_frac = int.from_bytes(data[10:14], byteorder='little')
            devices[mac_address]['ntp_timestamp'] = [ntp_timestamp, ntp_timestamp_frac]
            nominal_sample_rate = struct.unpack('f', data[118:122])[0]
            devices[mac_address]['nominal_sample_rate'] = nominal_sample_rate
            devices[mac_address]['range'] = data[122]

            #Choose the offsets and scales based upon the sample rate
            devices[mac_address]['x_scale'] = devices[mac_address]['x_scale'][str(nominal_sample_rate)]
            devices[mac_address]['y_scale'] = devices[mac_address]['y_scale'][str(nominal_sample_rate)]
            devices[mac_address]['z_scale'] = devices[mac_address]['z_scale'][str(nominal_sample_rate)]
            devices[mac_address]['x_offset'] = devices[mac_address]['x_offset'][str(nominal_sample_rate)]
            devices[mac_address]['y_offset'] = devices[mac_address]['y_offset'][str(nominal_sample_rate)]
            devices[mac_address]['z_offset'] = devices[mac_address]['z_offset'][str(nominal_sample_rate)]
            
        devices[mac_address]['data'] = []
        devices[mac_address]['micros'] =  int.from_bytes(data[14:18], byteorder='little')
        devices[mac_address]['packet_num'] = int.from_bytes(data[114:118], byteorder='little')
        for q in range(___grab_length___):
            x = int.from_bytes(data[18+6*q+0:18+6*q+2], byteorder='little', signed=True)
            y = int.from_bytes(data[18+6*q+2:18+6*q+4], byteorder='little', signed=True)
            z = int.from_bytes(data[18+6*q+4:18+6*q+6], byteorder='little', signed=True)
            devices[mac_address]['data'].append([x,y,z])
        
        with open(data_file, "w") as fh:
                json.dump(devices, fh, indent=1, sort_keys=True)
        return devices
    else:
        with open(data_file, "ab+") as fh:
                fh.write(data[:123])
        
    return 1


def dict2flac(d, flac_file, verbose=False):
    
    [ntp_timestamp, ntp_timestamp_frac] = d['ntp_timestamp']
    
    #The array containing microseconds since the Bluebox started may well be too long to easily store in metadata
    #so this will need to be stored as an additional channel
    
    #The accelerometer data is 16 bit, but the micros data is 32 bit, however there is only one micros data
    #for every 16 accelerometer data, so with some manipulation, we can easily store these data in an
    #additional channel
    #Because micros are unsigned and accelerometers are signed, we need to do some work when extracting them.
    micro_channel = np.zeros((d['data'].shape[0],1),dtype='int16')
    for idx, m in enumerate(d['micros']):
        micro_channel[2*idx]   = (m >> 16) & 0xffff
        micro_channel[2*idx+1] = m & 0xffff
        
    a = np.append(d['data'], micro_channel, axis=1)
        
    soundfile.write(flac_file,a,int(np.round(d['sample_rate'])))
    if verbose:
        print(flac_file)
    audio = FLAC(flac_file)
    audio["device_id"] = str(d['id'])
    audio["title"] = '"' + d['title'] + '"'
    audio["recorded"] = d['recorded']
    audio["ntp_timestamp"] = str(ntp_timestamp)
    audio["ntp_timestamp_frac"] = str(ntp_timestamp_frac)
    audio["range"] = str(d['range'])
    audio["sample_rate"] = str(d['sample_rate'])
    audio["nominal_sample_rate"] = str(d['nominal_sample_rate'])
    audio["x_scale"] = str(d['x_scale'])
    audio["y_scale"] = str(d['y_scale'])
    audio["z_scale"] = str(d['z_scale'])
    audio["x_offset"] = str(d['x_offset'])
    audio["y_offset"] = str(d['y_offset'])
    audio["z_offset"] = str(d['z_offset'])
    
    audio.save()
    if verbose:
        audio.pprint()

def gather_data(
    num_seconds=___default_num_seconds___,
    title=___default_title___,
    directory=___default_directory___,
    calibration_file=___default_calibration___,
    live=False,
    verbose=False,
    udpip=False,
    port=False,
    ):
    """Gather a segment of data from an ADXL345 accelerometer and store it in a timestamped flac file.
    
    Keyword arguments:
    num_seconds      -- number of seconds of data to grab
    title            -- a description of the recorded data
    directory        -- directory to store the flac file (use '--' to just create a dictionary of output)
    calibration_file -- file with calibration data for the ADXL345 chip
    live             -- if True, simply overwrite temporary file with latest data 
    verbose          -- if True, display some information while processing
    udpip            -- if given, use this IP for UDP
    port             -- UDP port (default: 5005)
    
    """

    # -----------------------------------------------------------------------
    # Initialize some various variables
    #------------------------------------------------------------------------

    #Get the current computer's ip address (assumes an internet connection)
    if udpip:
        UDP_IP = udpip
    else:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        UDP_IP = s.getsockname()[0]
        s.close()

    if port:
        UDP_PORT = int(port)
    else:
        UDP_PORT = 5005

    if verbose:
        print("listening on {}:{}".format(UDP_IP,UDP_PORT))

    #Create the UDP receiving UDP socket
    sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setblocking(1)
    sock.bind((UDP_IP, UDP_PORT))

    tempdir = tempfile.gettempdir() #Cross-platform, but slow
    #tempdir = '/run/shm'
    
    data_file = os.path.join(tempdir,'BlueBox_tmp.bin')
    #Clear the data_file, in case it is not empty
    with open(data_file, "wb") as fh:
        pass
    
    if live:
        try:
            with open(calibration_file, 'r') as f:
                devices = json.load(f)
        except:
            if verbose:
                print("No valid calibration file found")
            devices = {}
        run_file = os.path.join(tempdir,'BlueBox.run')
        with open(run_file, "wb") as fh:
            pass
        while os.path.isfile(run_file):
            devices = update_data(sock,data_file,live,devices)
        return devices
            
    if not directory == '--':
        #Make sure the output directory exists, and is writeable
        if not os.path.isdir(directory):        
            try:
                os.mkdir(directory)
            except PermissionError:
                print("You do not have permission to write to {}".format(directory))
                return
            except FileNotFoundError:
                print("The directory '{}' does not exist".format(os.path.dirname(directory)))
                return
        else:
            try:
                with open(os.path.join(directory,"__bluebox_test_file"), "wb") as fh:
                    pass
            except PermissionError:
                print("You do not have permission to write to {}".format(directory))
                return
            os.unlink(os.path.join(directory,"__bluebox_test_file"))

    #Get a timestamp
    now = datetime.datetime.now()
    file_timestamp = now.strftime("%Y%m%d%H%M%S")

    number_points_grabbed = 0    
    start_time = time.monotonic()
    while (time.monotonic() < start_time + num_seconds) or (number_points_grabbed < 32):
        number_points_grabbed += ___grab_length___*update_data(sock,data_file)
        
    if verbose:
        print("We grabbed {} data points".format(number_points_grabbed))

    try:
        with open(calibration_file, 'r') as f:
            devices = json.load(f)
    except:
        if verbose:
            print("No valid calibration file found")
        devices = {}

    #We now extract the binary data and place it in a python dictionary
    chunk_size = 123
    with open(data_file, 'rb') as f:
        for chunk in iter(lambda: f.read(chunk_size), b''):
            s = binascii.hexlify(chunk[0:6]).decode('ascii')
            mac_address = ':'.join(a+b for a,b in zip(s[::2], s[1::2]))
            if mac_address not in devices:
                if verbose:
                    print("Adding {} to devices".format(mac_address))
                devices[mac_address] = {}
                devices[mac_address]['x_scale'] = {"12.5":256,"25.0":256,"50.0":256,"100.0":256,"200.0":256,"400.0":256,"800.0":256,"1600.0":256,"3200.0":256}
                devices[mac_address]['y_scale'] = {"12.5":256,"25.0":256,"50.0":256,"100.0":256,"200.0":256,"400.0":256,"800.0":256,"1600.0":256,"3200.0":256}
                devices[mac_address]['z_scale'] = {"12.5":256,"25.0":256,"50.0":256,"100.0":256,"200.0":256,"400.0":256,"800.0":256,"1600.0":256,"3200.0":256}
                devices[mac_address]['x_offset'] = {"12.5":0,"25.0":0,"50.0":0,"100.0":0,"200.0":0,"400.0":0,"800.0":0,"1600.0":0,"3200.0":0}
                devices[mac_address]['y_offset'] = {"12.5":0,"25.0":0,"50.0":0,"100.0":0,"200.0":0,"400.0":0,"800.0":0,"1600.0":0,"3200.0":0}
                devices[mac_address]['z_offset'] = {"12.5":0,"25.0":0,"50.0":0,"100.0":0,"200.0":0,"400.0":0,"800.0":0,"1600.0":0,"3200.0":0}
                devices[mac_address]['id'] = 50 + len(devices)
            if not 'ntp_timestamp' in devices[mac_address]:            
                ntp_timestamp = int.from_bytes(chunk[6:10], byteorder='little')
                ntp_timestamp_frac = int.from_bytes(chunk[10:14], byteorder='little')
                devices[mac_address]['ntp_timestamp'] = [ntp_timestamp, ntp_timestamp_frac]
                devices[mac_address]['micros'] = []
                devices[mac_address]['packet_num'] = []                
                devices[mac_address]['data'] = []
                nominal_sample_rate = struct.unpack('f', chunk[118:122])[0]
                devices[mac_address]['nominal_sample_rate'] = nominal_sample_rate
                devices[mac_address]['range'] = chunk[122]
                devices[mac_address]['title'] = title
                devices[mac_address]['recorded'] = file_timestamp                

                #Choose the offsets and scales based upon the sample rate
                devices[mac_address]['x_scale'] = devices[mac_address]['x_scale'][str(nominal_sample_rate)]
                devices[mac_address]['y_scale'] = devices[mac_address]['y_scale'][str(nominal_sample_rate)]
                devices[mac_address]['z_scale'] = devices[mac_address]['z_scale'][str(nominal_sample_rate)]
                devices[mac_address]['x_offset'] = devices[mac_address]['x_offset'][str(nominal_sample_rate)]
                devices[mac_address]['y_offset'] = devices[mac_address]['y_offset'][str(nominal_sample_rate)]
                devices[mac_address]['z_offset'] = devices[mac_address]['z_offset'][str(nominal_sample_rate)]

            micros = int.from_bytes(chunk[14:18], byteorder='little')
            packet_num = int.from_bytes(chunk[114:118], byteorder='little')
            devices[mac_address]['micros'].append(micros)
            devices[mac_address]['packet_num'].append(packet_num)
            for q in range(___grab_length___):
                x = int.from_bytes(chunk[18+6*q+0:18+6*q+2], byteorder='little', signed=True)
                y = int.from_bytes(chunk[18+6*q+2:18+6*q+4], byteorder='little', signed=True)
                z = int.from_bytes(chunk[18+6*q+4:18+6*q+6], byteorder='little', signed=True)
                devices[mac_address]['data'].append([x,y,z])

    os.unlink(data_file)

    #Now we:
    #  check for dropped packets,
    #  calculate the sample rate,
    #  convert data to a numpy array
    dropped = False
    for key in devices:
        if 'ntp_timestamp' in devices[key]:
            d = devices[key]
            #check if we have got more than one packet
            if len(d['packet_num']) == 1:
                devices[key]['sample_rate'] = d['nominal_sample_rate']
                devices[key]['data'] = np.array(devices[key]['data'],dtype='int16')
                continue
            #Check if there are any dropped packets
            packet_diff = np.diff(d['packet_num'])
            if np.max(packet_diff) > 1:
                dropped = True
                if verbose:
                    print("{} packets have been dropped".format(sum(p != 1 for p in packet_diff)))
                    for idx,x in enumerate(packet_diff):
                        if x > 1:
                            print("Packet {} has been dropped".format(idx))            
            sample_rate = 1/((d['micros'][-1]-d['micros'][0])/(len(d['micros'])-1)/16*1e-6)
            devices[key]['sample_rate'] = sample_rate
            devices[key]['data'] = np.array(devices[key]['data'],dtype='int16')

    if verbose:
        for key in devices:
            if 'ntp_timestamp' in devices[key]:
                d = devices[key]
                print("device id         : {}".format(d['id']))
                print("mac address       : {}".format(key))
                device_boot_time = d['ntp_timestamp'][0] + d['ntp_timestamp'][1]/2**32
                device_record_time = device_boot_time + d['micros'][0]/1.0e6
                print("device start      : {} {}:{}".format(
                      datetime.datetime.fromtimestamp(device_boot_time).strftime('%Y-%m-%d %H:%M:%S.%f'),
                      d['ntp_timestamp'][0],d['ntp_timestamp'][1]
                ))
                print("recorded (device) : {}".format(
                      datetime.datetime.fromtimestamp(device_record_time).strftime('%Y-%m-%d %H:%M:%S.%f')))                
                print("recorded (server) : {} {}".format(now.strftime('%Y-%m-%d %H:%M:%S.%f'),file_timestamp))
                print("title             : {}".format(title))
                print("sample rate       : {}".format(d['sample_rate']))
                print("nominal rate      : {}".format(d['nominal_sample_rate']))
                print("range             : {}".format(d['range']))
                print("x_scale           : {}".format(d['x_scale']))
                print("y_scale           : {}".format(d['y_scale']))
                print("z_scale           : {}".format(d['z_scale']))
                print("x_offset          : {}".format(d['x_offset']))
                print("y_offset          : {}".format(d['y_offset']))
                print("z_offset          : {}".format(d['z_offset']))
                num_el = 3
                print("x data            : [{} ... {}]".format(
                    ", ".join([str(a) for a in d['data'][:num_el,0]]),
                    ", ".join([str(a) for a in d['data'][-num_el:,0]])
                ))
                print("y data            : [{} ... {}]".format(
                    ", ".join([str(a) for a in d['data'][:num_el,1]]),
                    ", ".join([str(a) for a in d['data'][-num_el:,1]])
                ))
                print("z data            : [{} ... {}]".format(
                    ", ".join([str(a) for a in d['data'][:num_el,2]]),
                    ", ".join([str(a) for a in d['data'][-num_el:,2]])
                ))
                print("microseconds      : {}".format(d['micros'][:6]) )

    if directory == '--':
            
        return dropped, devices
        
    #We now need to write the data to one (or more) flac file(s)
    flac_files = []    
    for key in devices:
        if 'ntp_timestamp' in devices[key]:
            d = devices[key]
            device_id = d['id']
            flac_file = os.path.join(directory,"bluebox_{:02d}_{}.flac".format(device_id,file_timestamp))
            dict2flac(d, flac_file, verbose)
            flac_files.append(flac_file)
            
    return dropped, flac_files
            
try:
    get_ipython()
except:
    if (__name__ == '__main__'):

        help_text = __doc__

        parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter, description=help_text)
        parser.add_argument("-n", '--num_seconds', help="Number of seconds of data to record", type=int, default=___default_num_seconds___)
        parser.add_argument("-t", '--title', help="Description of data", type=str, default=___default_title___)
        parser.add_argument("-d", '--directory', help="Directory to store the flac file (use '--' to just create a dictionary of output)", type=str, default=___default_directory___)
        parser.add_argument("-c", '--calibration', help="ADXL345 calibration file", type=str, default=___default_calibration___)
        parser.add_argument("-l", '--live', help="if True, simply overwrite temporary file with latest data", action='store_true')
        parser.add_argument("-v", '--verbose', help="Show some output", action='store_true') 
        parser.add_argument("-u", '--udpip', help="IP address used for UDP", type=str) 
        parser.add_argument("-u", '--port', help="port used for UDP", type=str) 
        args = parser.parse_args()
        gather_data(args.num_seconds,args.title,args.directory,args.calibration,args.live,args.verbose,args.udpip,args.port)
