#!/bin/python3
#https://github.com/andrea-varesio/vanity-PyGP

import argparse
import datetime
import os
import shutil
import sys
import tempfile
import time

from contextlib import contextmanager

import gpg
import wget

from cryptography.fernet import Fernet
from secure_delete import secure_delete

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
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--filter', type=str,
                        help='Find a key with ID matching this filter')
    parser.add_argument('-n', '--name', type=str,
                        help='Specify the uid name')
    parser.add_argument('-e', '--email', type=str,
                        help='Specify the uid email')
    parser.add_argument('-p', '--path', type=str,
                        help='Specify a path to save the generated key')
    parser.add_argument('-q', '--quiet', action='store_true',
                        help='Disable the majority of prompts and verbosity')
    parser.add_argument('--disable-stats', action='store_true',
                        help='Disable stats every 10 seconds')
    parser.add_argument('--signing-key', action='store_true',
                        help='Add sign capability to the master key')
    parser.add_argument('-c', '--check-entropy', action='store_true',
                        help='Check the available entropy, then exit')
    return parser.parse_args()

def get_entropy():
    with open('/proc/sys/kernel/random/entropy_avail','r') as entropy_avail:
        entropy = int(entropy_avail.readlines()[0])
    return entropy

def check_entropy():
    entropy = get_entropy()
    if entropy<2000:
        if not args.quiet:
            print('Entropy: ',entropy)
            print('Not enough entropy')
            print('Trying again in 60 seconds')
            print('Use this time to type as many random characters as possible\n')
            time.sleep(60)
            entropy = get_entropy()
            if entropy<2000:
                print('\nEntropy: ',entropy)
                print('Not enough entropy')
                print('Try again when the entropy is above 2000')
                print('You can check the available entropy with "generate.py -e"')
                print('Exiting...')
                sys.exit(1)
            else:
                print('\n\n\n')
        else:
            sys.exit(1)

def print_stats():
    print(f'Elapsed time: {str(now - start)} | Try #{str(i)}')

def generate_encryption_key(keyfile_path):
    encryption_key = Fernet.generate_key()
    with open(keyfile_path, 'wb') as keyfile_data:
        keyfile_data.write(encryption_key)

def load_encryption_key(keyfile_path):
    return open(keyfile_path, 'rb').read()

def encrypt_secret_key():
    encrypted_file_path = os.path.join(savedir, f'encrypted-secretkey-0x{keyid}.key')
    k = Fernet(load_encryption_key(keyfile))
    encrypted_data = k.encrypt(gpg_context.key_export_secret(pattern=fingerprint))
    with open(encrypted_file_path, 'wb') as encrypted_file:
        encrypted_file.write(encrypted_data)
    secure_permissions(os.path.join(savedir, f'encrypted-secretkey-0x{keyid}.key'))

def encrypt(unencrypted_file):
    encrypted_file_path = os.path.join(savedir, f'encrypted-{os.path.basename(unencrypted_file)}')
    k = Fernet(load_encryption_key(keyfile))
    with open(unencrypted_file, 'rb') as unencrypted_data:
        encrypted_data = k.encrypt(unencrypted_data.read())
    with open(encrypted_file_path, 'wb') as encrypted_file:
        encrypted_file.write(encrypted_data)

def secure_permissions(file):
    os.chmod(file, 0o600)

@contextmanager
def suppress_stdout():
    with open(os.devnull, "w") as devnull:
        old_stdout = sys.stdout
        sys.stdout = devnull
        try:
            yield
        finally:
            sys.stdout = old_stdout

args = parse_arguments()

if args.check_entropy:
    print('Entropy :', get_entropy())
    sys.exit(0)

check_entropy()

now = datetime.datetime.now()
timestamp = (now.strftime('_%Y%m%d_%H%M%S'))

with tempfile.TemporaryDirectory(prefix='gnupg_', suffix=timestamp) as GNUPGHOME:

    gpg_context = gpg.Context(armor=True, offline=True, home_dir=GNUPGHOME)

    if not args.quiet:
        print('Downloading gpg.conf')
    with suppress_stdout():
        wget.download(
            'https://raw.githubusercontent.com/drduh/config/master/gpg.conf',
            GNUPGHOME, bar=None
        )

    if not args.quiet:
        print(
            '\n\nIt is now recommended that you DISABLE networking for the remainder of the process'
        )
        input('Press ENTER to continue\n')

    if args.path is None:
        savedir = os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            f'generated_keys{timestamp}'
        )
    elif os.path.isdir(args.path):
        savedir = os.path.join(args.path, f'generated_keys{timestamp}')
    else:
        if not args.quiet:
            print('Invalid path')
        sys.exit(1)
    os.mkdir(savedir)

    if args.filter is not None:
        key_filter = args.filter
    else:
        input('\nEnter the filter you want to look for: ')

    if args.name is not None:
        realname = args.name
    else:
        realname = input('\nEnter your Name: ')

    if args.email is not None:
        email = args.email
    else:
        email = input('Enter your Email: ')

    userid = realname + ' <' + email + '>'

    keyfile = os.path.join(savedir, 'encryption-key.key')
    generate_encryption_key(keyfile)
    secure_permissions(keyfile)

    i = 0
    start = datetime.datetime.now()
    last = start

    while True:
        dmkey = gpg_context.create_key(
            userid, algorithm='ed25519', expires=False,
            sign=args.signing_key, certify=True, force=True
        )
        fingerprint = format(dmkey.fpr)
        now = datetime.datetime.now()
        i += 1
        if fingerprint[-len(key_filter):] == key_filter:
            break
        if (now - last) > datetime.timedelta(seconds=10):
            last = now
            shutil.rmtree(os.path.join(GNUPGHOME, 'private-keys-v1.d'))
            os.mkdir(os.path.join(GNUPGHOME, 'private-keys-v1.d'))
            shutil.rmtree(os.path.join(GNUPGHOME, 'openpgp-revocs.d'))
            os.remove(os.path.join(GNUPGHOME, 'pubring.kbx~'))
            os.remove(os.path.join(GNUPGHOME, 'pubring.kbx'))
            if not args.disable_stats:
                print_stats()

    if not args.quiet:
        print('\nMATCH FOUND: ' + fingerprint)

    if not args.disable_stats:
        print_stats()

    key = gpg_context.get_key(dmkey.fpr, secret=True)
    keyid = fingerprint[-16:]
    keygrip = str(key).partition('keygrip=\'')[2][:40]

    with open(os.path.join(savedir, f'publickey-0x{keyid}.asc'), 'wb') as public_key:
        public_key.write(gpg_context.key_export(pattern=fingerprint))

    encrypt_secret_key()

    encrypt(os.path.join(GNUPGHOME, 'private-keys-v1.d', f'{keygrip}.key'))
    secure_permissions(os.path.join(savedir, f'encrypted-{keygrip}.key'))

    encrypt(os.path.join(GNUPGHOME, 'openpgp-revocs.d', f'{fingerprint}.rev'))
    secure_permissions(os.path.join(savedir, f'encrypted-{fingerprint}.rev'))

    with suppress_stdout():
        shutil.copy('decrypt.py', savedir)

    if not args.quiet:
        print('\nSecurely erasing tmp files...')
    secure_delete.secure_random_seed_init()
    secure_delete.secure_delete(os.path.join(GNUPGHOME, 'private-keys-v1.d', f'{keygrip}.key'))
    secure_delete.secure_delete(os.path.join(GNUPGHOME, 'openpgp-revocs.d', f'{fingerprint}.rev'))
