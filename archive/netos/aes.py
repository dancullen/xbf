# aes.py Demonstrates how to perform AES encryption and decryption.
#
# https://www.pycryptodome.org/en/latest/src/cipher/aes.html
# https://www.pycryptodome.org/en/latest/src/examples.html#encrypt-data-with-aes
# https://nvlpubs.nist.gov/nistpubs/Legacy/SP/nistspecialpublication800-38a.pdf - Contains sample data at the end!
#
# Note that AES-128 means that the key is 128 bits (16 bytes) long.
# In CFB mode, the initialization vector (IV) is the same length as the key.
#
# According to RFC 3826, SNMP uses CFB mode of AES, with S=128 feedback bits. In other words, CFB128.
# So that means the `segment_size` parameter of Cryptodome.Cipher.AES.new() should be 128.
#
# msgAuthoritativeEngineBoots is the value packed in the message from the SNMP Manager to the SNMP Agent.
# snmpEngineBoots is the value packed in the message from the SNMP Agent to the SNMP Manager
#
# The privacy (encryption) password is a shared secret between the Manager and the Agent.
#
# Questions:
# - How is the passphrase turned into a key?
# - How is the initialization vector determined?
#   - See RFC 3826. "The 128-bit IV is obtained as the concatenation of the
#     authoritative SNMP engine's 32-bit snmpEngineBoots, the SNMP engine's 32-bit snmpEngineTime,
#     and a local 64-bit integer."
#     Dan: The 64-bit integer os the msgPrivacyParameters field.
# - What is the engine ID?
# - How is the encryptkey (20 bytes for SHA-1) converted to the 16-bit AES encryption key?
#   Answer: The first 128 bits of the localized key (Kul) are used as the AES encryption key.
#   So in other words, we just ignore everything after the first 16 bytes.
#   Source: Section 3.1.2.1 of RFC 3826.

import base64
import binascii
#import struct

from Cryptodome.Cipher import AES
from Cryptodome.Random import get_random_bytes
#import pyasn1


def calculate_localized_privacy_key(password, engineID):
    # calculate_localized_privacy_key converts the given password and engine ID to the localized SNMP privacy key 
    # used for encryption and decryption. The inputs are both 'bytes' objects, not ascii hex strings,
    # and similarly for the returned value.
    #
    # The algorithm is described in RFC 3826 Section 1.2 "Key Localization", which references RFC 3414 Section 2.6.
    # Basically we just use the SHA hash function to hash the plaintext password in a certain way.
    # Some sample code can be found in Section A.2.2 of RFC 3414.
    #
    # Note that AES-128 requires a 16-byte key. But a SHA-1 hash contains a 20-byte key.
    # How do we reconcile this?
    #
    # An example of converting the password and snmp Engine ID to a key can be found in
    # Section A.3.2. of RFC 3414. See test_calculate_localized_privacy_key() below for that data.
    #
    # The implementation below is based on [SNMPv3-Hash-Generator code](https://github.com/TheMysteriousX/SNMPv3-Hash-Generator).
    # 
    # Additional test data for us to check our implementation against can be generated like this:
    #   $ pip install SNMPv3-Hash-Generator
    #   $ snmpv3-hashgen.exe --mode priv --user bootstrap --auth temp_password --priv temp_password --engine 80001f88805cb68a3d7a35725e00000000
    #   User: bootstrap
    #   Auth: temp_password / db329cce02a91ae1da5251b167d04f302327fa3e
    #   Priv: temp_password / db329cce02a91ae1da5251b167d04f302327fa3e
    #   Engine: 80001f88805cb68a3d7a35725e00000000
    #   ESXi USM String: bootstrap/db329cce02a91ae1da5251b167d04f302327fa3e/db329cce02a91ae1da5251b167d04f302327fa3e/priv

    import hashlib
    from itertools import repeat

    # Basically you just keep looping through the password buffer, updating your hash with each byte.
    # This Python implementation does this succinctly by creating a big buffer with the passphrase
    # replicated many times, then hashing the entire buffer in one shot. But a C implementation with loops
    # that resembles the example in A.2.2 of RFC 3414 works too.

    num = 1048576  # Section A.2.2 of RFC 3414 says that we keep hashing until we've done 1 MB (i.e., 1*1024*1024=1048576 bytes)
    reps = num // len(password) + 1  # The +1 ensures that we'll have at least 1 MB of data in our expanded buffer.
    expanded = b''.join(list(repeat(password, reps)))[:num]
    Ku = hashlib.sha1(expanded).digest()

    E = engineID

    Kul_priv = b"".join([Ku, E, Ku])

    return hashlib.sha1(Kul_priv).digest()


def test_calculate_localized_privacy_key():
    password = b"maplesyrup"
    snmpEngineID = binascii.unhexlify("000000000000000000000002")

    expected_key = binascii.unhexlify("6695febc9288e36282235fc7151f128497b38f3f")

    key = calculate_localized_privacy_key(password, snmpEngineID)

    assert expected_key == key


def test_length_of_ciphertext():
    # Demonstrates that the CFB128-AES128 encryption algorithm generates ciphertext output
    # that is the same length (in bytes) as the plaintext input. In other words, even
    # if we use a small payload (smaller than the 16 bytes, which is the key length
    # as well as the initialization vector length), this still holds true.

    key = get_random_bytes(16)
    iv = get_random_bytes(16)

    plaintext = b"hello"

    cipher = AES.new(key=key, mode=AES.MODE_CFB, iv=iv, segment_size=128)
    ciphertext = cipher.encrypt(plaintext)
    assert len(ciphertext) == len(plaintext)  # This test provdes

    print("test_length_of_ciphertext results:")
    print("key:        %s" % binascii.hexlify(key))
    print("iv:         %s" % binascii.hexlify(iv))
    print("plaintext:  %s (%s)" % (binascii.hexlify(plaintext), plaintext))
    print("ciphertext: %s (%s)" % (binascii.hexlify(ciphertext), ciphertext))


def test_cfb128_aes128_nist_example():
    # Demo data from Section F.3.13 "CFB128-AES128.Encrypt" of /nistspecialpublication800-38a.pdf.
    key = binascii.unhexlify("2b7e151628aed2a6abf7158809cf4f3c")
    iv = binascii.unhexlify("000102030405060708090a0b0c0d0e0f")
    plaintext = binascii.unhexlify("6bc1bee22e409f96e93d7e117393172a")
    expected_ciphertext = binascii.unhexlify("3b3fd92eb72dad20333449f8e83cfb4a")

    cipher = AES.new(key=key, mode=AES.MODE_CFB, iv=iv, segment_size=128)
    ciphertext = cipher.encrypt(plaintext)
    assert expected_ciphertext == ciphertext


def test_net_snmp_aes128_test_data_from_wireshark():
    # Demo data captured with Wireshark while running a loopback test with net-SNMP
    # on my Ubuntu machine, using AES for SNMP privacy.

    print("Test Case 1: Data from SNMP Manager to SNMP Agent.")
    privacyPassword = b"temp_password"
    msgUserName = b"bootstrap"
    msgAuthoritativeEngineID = binascii.unhexlify("80001f88805cb68a3d7a35725e00000000")
    msgAuthoritativeEngineBoots = binascii.unhexlify("00000008")
    msgAuthoritativeEngineTime = binascii.unhexlify("0018aaa3")
    msgPrivacyParameters = binascii.unhexlify("a3d2de8298556609")
    ciphertext = binascii.unhexlify("0efade116eecc46fcfa4e680bf65418331371363d79c4d216ecee14ff62af6f00a33ba8b49c00271902c857574f0e585c50d94e7d4")
    expected_plaintext =  binascii.unhexlify("3033041180001f88805cb68a3d7a35725e000000000400a01c02043197f9d9020100020100300e300c06082b060102010101000500")

    iv = msgAuthoritativeEngineBoots + msgAuthoritativeEngineTime + msgPrivacyParameters  # 4 bytes + 4 bytes + 4 bytes = 16 bytes total.
    key = calculate_localized_privacy_key(privacyPassword, msgAuthoritativeEngineID)
    key = key[0:16]  # Use only the first 16 bytes of the 20-byte key. Per Section 3.1.2.1 of RFC 3826.

    cipher = AES.new(key=key, mode=AES.MODE_CFB, iv=iv, segment_size=128)
    plaintext = cipher.decrypt(ciphertext)

    print("iv:                  %s (%d)" % (binascii.hexlify(iv), len(iv)))
    print("key:                 %s (%d)" % (binascii.hexlify(key), len(key)))
    print("ciphertext:          %s" % binascii.hexlify(ciphertext))
    print("expected_plaintext:  %s" % binascii.hexlify(expected_plaintext))
    print("plaintext:           %s" % binascii.hexlify(plaintext))

    assert expected_plaintext == plaintext

    print("Test Case 2: SNMP Agent to the SNMP Manager.")
    msgAuthoritativeEngineID = binascii.unhexlify("80001f88805cb68a3d7a35725e00000000")
    msgAuthoritativeEngineBoots = binascii.unhexlify("00000008")
    msgAuthoritativeEngineTime = binascii.unhexlify("0018aaa3") 
    msgPrivacyParameters = binascii.unhexlify("dfe5df215b458720")
    ciphertext = binascii.unhexlify("571e8cb59a7782378ad6bf6387b08169224ad6a9ae751cb959d1bf8f4e716ad9fa1dc7734699e8b34a54402feeff787b1f50576f40a0f1b51c1af99e13c8e8ed19174a2cdc7802259d3bf95073a3fa0c6b3849367da980ec73ac5d6fdacdd98224b400d2ffaf5293b6d65dcc77c974c8e39f1581b9035553ee31299235802ecd7e578223c2")
    expected_plaintext = binascii.unhexlify("308182041180001f88805cb68a3d7a35725e000000000400a26b02043197f9d9020100020100305d305b06082b06010201010100044f4c696e7578206c756e6120342e31352e302d37362d67656e65726963202338362d5562756e747520534d5020467269204a616e2031372031373a32343a3238205554432032303230207838365f3634")

    iv = msgAuthoritativeEngineBoots + msgAuthoritativeEngineTime + msgPrivacyParameters
    key = calculate_localized_privacy_key(privacyPassword, msgAuthoritativeEngineID)
    key = key[0:16]  # Use only the first 16 bytes of the 20-byte key. Per Section 3.1.2.1 of RFC 3826.

    cipher = AES.new(key=key, mode=AES.MODE_CFB, iv=iv, segment_size=128)
    plaintext = cipher.decrypt(ciphertext)

    print("iv:                  %s (%d)" % (binascii.hexlify(iv), len(iv)))
    print("key:                 %s (%d)" % (binascii.hexlify(key), len(key)))
    print("ciphertext:          %s" % binascii.hexlify(ciphertext))
    print("expected_plaintext:  %s" % binascii.hexlify(expected_plaintext))
    print("plaintext:           %s" % binascii.hexlify(plaintext))

    assert expected_plaintext == plaintext


def main():
    test_calculate_localized_privacy_key()    
    test_length_of_ciphertext()
    test_cfb128_aes128_nist_example()
    test_net_snmp_aes128_test_data_from_wireshark()


if __name__ == "__main__":
    main()
