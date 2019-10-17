import os
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

def pad(plaintext):
    padded = bytearray(plaintext)
    padded.append(1)
    for x in range(0, 4):
        padded.append(0)
    return bytes(padded)

#AES

def AESEncrypt(plaintext, key, iv):
    plaintext = pad(plaintext)
    backend = default_backend()
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=backend)
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(plaintext) + encryptor.finalize()
    return ciphertext

def AESDecrypt(ciphertext, key, iv):
    backend = default_backend()
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=backend)
    decryptor = cipher.decryptor()
    plaintext = decryptor.update(ciphertext) + decryptor.finalize()
    plaintext = plaintext[0:123]
    return plaintext

#Camellia

def CamelliaEncrypt(plaintext, key, iv):
    plaintext = pad(plaintext)
    backend = default_backend()
    cipher = Cipher(algorithms.Camellia(key), modes.CBC(iv), backend=backend)
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(plaintext) + encryptor.finalize()
    return ciphertext

def CamelliaDecrypt(ciphertext, key, iv):
    backend = default_backend()
    cipher = Cipher(algorithms.Camellia(key), modes.CBC(iv), backend=backend)
    decryptor = cipher.decryptor()
    plaintext = decryptor.update(ciphertext) + decryptor.finalize()
    plaintext = plaintext[0:123]
    return plaintext

#CAST5

def CAST5Encrypt(plaintext, key, iv):
    plaintext = pad(plaintext)
    backend = default_backend()
    cipher = Cipher(algorithms.CAST5(key), modes.CBC(iv), backend=backend)
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(plaintext) + encryptor.finalize()
    return ciphertext

def CAST5Decrypt(ciphertext, key, iv):
    backend = default_backend()
    cipher = Cipher(algorithms.CAST5(key), modes.CBC(iv), backend=backend)
    decryptor = cipher.decryptor()
    plaintext = decryptor.update(ciphertext) + decryptor.finalize()
    plaintext = plaintext[0:123]
    return plaintext

#ChaCha20

def ChaChaEncrypt(plaintext, key, nonce):
    algorithm = algorithms.ChaCha20(key, nonce)
    cipher = Cipher(algorithm, mode=None, backend=default_backend())
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(plaintext)
    return ciphertext
    
def ChaChaDecrypt(ciphertext, key, nonce):
    algorithm = algorithms.ChaCha20(key, nonce)
    cipher = Cipher(algorithm, mode=None, backend=default_backend())
    decryptor = cipher.decryptor()
    plaintext = decryptor.update(ciphertext)
    return plaintext

#SEED

def SEEDEncrypt(plaintext, key, iv):
    plaintext = pad(plaintext)
    backend = default_backend()
    cipher = Cipher(algorithms.SEED(key), modes.CBC(iv), backend=backend)
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(plaintext) + encryptor.finalize()
    return ciphertext

def SEEDDecrypt(ciphertext, key, iv):
    backend = default_backend()
    cipher = Cipher(algorithms.SEED(key), modes.CBC(iv), backend=backend)
    decryptor = cipher.decryptor()
    plaintext = decryptor.update(ciphertext) + decryptor.finalize()
    plaintext = plaintext[0:123]
    return plaintext