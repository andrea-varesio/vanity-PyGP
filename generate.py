#!/bin/python3
#https://github.com/andrea-varesio/vanity-PyGP

import argparse
import datetime
import gpg
import os
import shutil
import subprocess
import sys
import tempfile
import time
import wget
from contextlib import contextmanager
from cryptography.fernet import Fernet
from secure_delete import secure_delete

def license():
    print('\n**************************************************')
    print('"Vanity PyGP" - Securely generate PGP keys with a custom ID.')
    print('Copyright (C) 2022 Andrea Varesio (https://www.andreavaresio.com/).')
    print('This program comes with ABSOLUTELY NO WARRANTY')
    print('This is free software, and you are welcome to redistribute it under certain conditions')
    print('Full license available at https://github.com/andrea-varesio/vanity-PyGP')
    print('**************************************************\n\n')

def parser():
    parser = argparse.ArgumentParser(description='Securely generate PGP keys with a custom ID')
    parser.add_argument('-f', '--filter', help='Find a key with ID matching this filter', type=str)
    parser.add_argument('-n', '--name', help='Specify the uid name', type=str)
    parser.add_argument('-e', '--email', help='Specify the uid email', type=str)
    parser.add_argument('-p', '--path', help='Specify a path to save the generated key', type=str)
    parser.add_argument('-q', '--quiet', help='Disable the majority of prompts and verbosity', action='store_true')
    parser.add_argument('--disable-stats', help='Disable stats every 10 seconds', action='store_true')
    parser.add_argument('--signing-key', help='Add sign capability to the master key', action='store_true')
    parser.add_argument('-c', '--check-entropy', help='Check the available entropy, then exit', action='store_true')
    return parser.parse_args()

def getEntropy():
    f = open('/proc/sys/kernel/random/entropy_avail','r')
    entropy = int(f.readlines()[0])
    f.close()
    return entropy

def checkEntropy():
    entropy = getEntropy()
    if entropy<2000:
        if args.quiet == False:
            print('Entropy: ',entropy)
            print('Not enough entropy')
            print('Trying again in 60 seconds')
            print('Use this time to type as many random characters as possible\n')
            time.sleep(60)
            entropy = getEntropy()
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
    entropy = getEntropy()
    print(f'Elapsed time: {str(now - start)} | Entropy: {str(entropy)} | Try #{str(i)}')

def generate_encryption_key(keyfile):
    encryption_key = Fernet.generate_key()
    with open(keyfile, 'wb') as keyfile:
        keyfile.write(encryption_key)

def load_encryption_key(keyfile):
    return open(keyfile, 'rb').read()

def encrypt_secret_key():
    encrypted_file = os.path.join(savedir, f'encrypted-secretkey-0x{keyid}.key')
    k = Fernet(load_encryption_key(keyfile))
    encrypted_data = k.encrypt(c.key_export_secret(pattern=fingerprint))
    with open(encrypted_file, 'wb') as encrypted_file:
        encrypted_file.write(encrypted_data)
    secure_permissions(os.path.join(savedir, f'encrypted-secretkey-0x{keyid}.key'))

def encrypt(unencrypted_file):
    encrypted_file = os.path.join(savedir, f'encrypted-{os.path.basename(unencrypted_file)}')
    k = Fernet(load_encryption_key(keyfile))
    encrypted_data = k.encrypt(open(unencrypted_file, 'rb').read())
    with open(encrypted_file, 'wb') as encrypted_file:
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

args = parser()

if args.check_entropy:
    print('Entropy :', getEntropy())
    sys.exit(0)

if args.quiet == False:
    license()

checkEntropy()

now = datetime.datetime.now()
timestamp = (now.strftime('_%Y%m%d_%H%M%S'))

with tempfile.TemporaryDirectory(prefix='gnupg_', suffix=timestamp) as GNUPGHOME:

    c = gpg.Context(armor=True, offline=True, home_dir=GNUPGHOME)

    if args.quiet == False:
        print('Downloading gpg.conf')
    with suppress_stdout():
        wget.download('https://raw.githubusercontent.com/drduh/config/master/gpg.conf', GNUPGHOME, bar=None)

    if args.quiet == False:
        print('\n\nIt is now recommended that you DISABLE networking for the remainder of the process')
        input('Press ENTER to continue\n')

    if args.path == None:
        savedir = os.path.join(os.path.dirname(os.path.realpath(__file__)), f'generated_keys{timestamp}')
    elif os.path.isdir(args.path):
        savedir = os.path.join(args.path, f'generated_keys{timestamp}')
    else:
        if args.quiet == False:
            print('Invalid path')
        sys.exit(1)
    os.mkdir(savedir)

    if args.filter != None:
        filter = args.filter
    else:
        input('\nEnter the filter you want to look for: ')

    if args.name != None:
        realname = args.name
    else:
        realname = input('\nEnter your Name: ')

    if args.email != None:
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
        dmkey = c.create_key(userid, algorithm='ed25519', expires=False, sign=args.signing_key, certify=True, force=True)
        fingerprint = format(dmkey.fpr)
        now = datetime.datetime.now()
        i += 1
        if fingerprint[-len(filter):] == filter:
            break
        elif (now - last) > datetime.timedelta(seconds=10):
            last = now
            checkEntropy()
            shutil.rmtree(os.path.join(GNUPGHOME, 'private-keys-v1.d'))
            os.mkdir(os.path.join(GNUPGHOME, 'private-keys-v1.d'))
            shutil.rmtree(os.path.join(GNUPGHOME, 'openpgp-revocs.d'))
            os.remove(os.path.join(GNUPGHOME, 'pubring.kbx~'))
            os.remove(os.path.join(GNUPGHOME, 'pubring.kbx'))
            if not args.disable_stats:
                print_stats()

    if args.quiet == False:
        print('\nMATCH FOUND: ' + fingerprint)

    if not args.disable_stats:
        print_stats()

    key = c.get_key(dmkey.fpr, secret=True)
    keyid = fingerprint[-16:]
    keygrip = str(key).partition('keygrip=\'')[2][:40]

    f = open(os.path.join(savedir, f'publickey-0x{keyid}.asc'), 'wb')
    f.write(c.key_export(pattern=fingerprint))
    f.close()

    encrypt_secret_key()

    encrypt(os.path.join(GNUPGHOME, 'private-keys-v1.d', f'{keygrip}.key'))
    secure_permissions(os.path.join(savedir, f'encrypted-{keygrip}.key'))

    encrypt(os.path.join(GNUPGHOME, 'openpgp-revocs.d', f'{fingerprint}.rev'))
    secure_permissions(os.path.join(savedir, f'encrypted-{fingerprint}.rev'))

    with suppress_stdout():
        shutil.copy('decrypt.py', savedir)

    if args.quiet == False:
        read('\nSecurely erasing tmp files...')
    secure_delete.secure_random_seed_init()
    secure_delete.secure_delete(os.path.join(GNUPGHOME, 'private-keys-v1.d', f'{keygrip}.key'))
    secure_delete.secure_delete(os.path.join(GNUPGHOME, 'openpgp-revocs.d', f'{fingerprint}.rev'))

if args.quiet == False:
    print('If you are in an ephemeral environment, make sure to save the keys somewhere safe and recoverable!')

if args.quiet == False:
    print('\nExiting...\n')
sys.exit(0)
