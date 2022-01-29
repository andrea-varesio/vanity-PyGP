#!/bin/python3
#https://github.com/andrea-varesio/vanity-PyGP

import argparse
import os
import sys

from cryptography.fernet import Fernet

def show_license():
    print('\n**************************************************')
    print('"Vanity PyGP" - Securely generate PGP keys with a custom ID.')
    print('Copyright (C) 2022 Andrea Varesio (https://www.andreavaresio.com/).')
    print('This program comes with ABSOLUTELY NO WARRANTY')
    print('This is free software, and you are welcome to redistribute it under certain conditions')
    print('Full license available at https://github.com/andrea-varesio/vanity-PyGP')
    print('**************************************************\n\n')

def parse_arguments():
    show_license()
    parser = argparse.ArgumentParser(description='Decrypt vanity-PyGP keys')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-a', '--all', help='Decrypt all files', action='store_true')
    group.add_argument('-f', '--file', help='Specify a file to decrypt', type=str)
    if len(sys.argv)==1:
        parser.print_help(sys.stderr)
        sys.exit(1)
    return parser.parse_args()

def load_encryption_key(keyfile_path):
    return open(keyfile_path, 'rb').read()

def create_decryption_dir(decryption_dir_path):
    if not os.path.isdir(decryption_dir_path):
        os.mkdir(decryption_dir_path)

def decrypt(encrypted_file, decrypted_file):
    k = Fernet(load_encryption_key(keyfile))
    with open(encrypted_file, 'rb') as encrypted_data:
        decrypted_data = k.decrypt(encrypted_data.read())
    with open(decrypted_file, 'wb') as decrypted_file:
        decrypted_file.write(decrypted_data)
    decrypted_data = None
    del decrypted_data

def secure_permissions(file):
    os.chmod(file, 0o600)

def start_decryption(encrypted_file):
    decrypted_file = os.path.join(
        decryption_dir,
        os.path.basename(encrypted_file).replace('encrypted-','')
    )
    decrypt(encrypted_file, decrypted_file)
    secure_permissions(decrypted_file)

args = parse_arguments()

keyfile = 'encryption-key.key'
if not os.path.isfile(keyfile):
    print('Missing encryption key. Cannot decrypt.')
    sys.exit(1)

decryption_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'decrypted')

if args.all:
    create_decryption_dir(decryption_dir)
    for encrypted_file in os.listdir(os.path.dirname(os.path.realpath(__file__))):
        if encrypted_file.startswith('encrypted-'):
            start_decryption(encrypted_file)
elif args.file is not None and os.path.isfile(args.file):
    create_decryption_dir(decryption_dir)
    encrypted_file = args.file
    start_decryption(encrypted_file)
elif args.file is not None:
    print('Invalid file provided')
    sys.exit(1)

sys.exit(0)
