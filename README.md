# Sarah_Connor_Thesis_Code
Code used for gathering data in my MPE Research Project

The code is split up into the two devices, Raspberry Pi and BlueBox. 

Within Raspberry Pi:
- Encryption Code - Contains import statements and code needed to run the algorithms. The files in here are imported by any files that need to encrypt or decrypt.
- Keys - Just contains the 128 bit and 256 bit key used.
- Load Code - Contains the code that was used for background sending (for light load) and background messaging (for heavy load).
- Raspberry Pi Code - Contains the code that is run on the Raspberry Pi Zero that runs the tests and sends the data back to a receiving laptop. 
- Receiver Notebooks - Contains the code that is run on the receiving laptop/computer while the tests are being run (checks that the encryption/decryption process was successful and saves data into a file)/

To run a test with Raspberry Pi (e.g. AES with light load):
1. On receiving computer, need relevant receiver notebook (e.g. AES in "Receiver Notebooks") along with the relevant key file (e.g. Key128 from "Keys" and encryption notebook (Encrypt_Decrypt_Functions from "Encrcyption Code") all in same folder. And run the notebook. Will wait for messages. 
2. On Raspberry Pi Zero, need relevant raspberry pi code (e.g. AES in "Raspberry Pi Code") along with the relevant key file (e.g. Key128 from "Keys" and encryption python file (Encrypt_Decrypt_Functions from "Encrcyption Code") all in same folder. And run the python file background-sending.py from "Load Code" in one terminal. 
3. In second terminal on Raspberry Pi Zero, run the AES.py code. 
4. Wait for data to be collected by the notebook on the receiver laptop. Will report if process was successful or not and save the timing data in a file. 

Within BlueBox:
- AES Receiver Code - Contains the updated gather.py file, now with an AES decryption step. This needs to be run with other SHL notebooks owned by the lab. 
- BlueBox Code - Contains folders AES, Acorn, AcornTest, Ascon, AsconTest, ChaCha, ChaChaTest, Speck and SpeckTest. Each of the "Test" folders contain a "Test" .ino file (e.g. AcornTest.ino) which tests if the encryption/decryption process works on the device. The other folders that do not have "Test" in their name contain the code in .ino files for collecting, encryption and sending the vibration data. These are adapted versions of the code already written by the SHL. Each of these folders also contains the relevant library folders from the Arduino Cryptography Library (https://github.com/rweather/arduinolibs).
