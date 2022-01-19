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

def parser():
    parser = argparse.ArgumentParser(description='Securely generate PGP keys with a custom ID')
    parser.add_argument('-f', '--filter', help='Find a key with ID matching this filter', type=str)
    parser.add_argument('-n', '--name', help='Specify the uid name', type=str)
    parser.add_argument('-e', '--email', help='Specify the uid email', type=str)
    parser.add_argument('-p', '--path', help='Specify a path to save the generated key, without creating a container. ie: /dev/sda1/', type=str)
    parser.add_argument('-s', '--stats', help='Print stats every 10 seconds', action='store_true')
    parser.add_argument('-q', '--quiet', help='Disable the majority of prompts and verbosity', action='store_true')
    parser.add_argument('--signing-key', help='Add sign capability to the master key', action='store_true')
    parser.add_argument('--no-dismount', help='Do not dismount the container when a match is found', action='store_true')
    parser.add_argument('--no-container', help='Skip the creation of an encrypted container', action='store_true')
    parser.add_argument('--python-only', help='Do not use any bash subprocess (Not yet implemented)', action='store_true')
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

def createVCcontainer():
    subprocess.run(
    r'''
        source var.tmp
        printf '\nCreating a new VeraCrypt container...\n'
        veracrypt -t -c --volume-type normal --size=500M --encryption=AES-Twofish-Serpent --hash=Whirlpool --filesystem=EXT4 --pim=0 --keyfiles="" vanity-pygp-$FILTER.hc
        printf '\nMounting the newly created container...\n'
        veracrypt -t -k "" --pim=0 --keyfiles="" --protect-hidden=no vanity-pygp-$FILTER.hc /media/veracrypt44
    '''
    , shell=True, check=True, executable='/bin/bash')

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
    print('\n**************************************************')
    print('"Vanity PyGP" - Securely generate PGP keys with a custom ID.')
    print('Copyright (C) 2022 Andrea Varesio (https://www.andreavaresio.com/).')
    print('This program comes with ABSOLUTELY NO WARRANTY')
    print('This is free software, and you are welcome to redistribute it under certain conditions')
    print('Full license available at https://github.com/andrea-varesio/vanity-PyGP')
    print('**************************************************\n\n')

checkEntropy()

now = datetime.datetime.now()
timestamp = (now.strftime('_%Y%m%d_%H%M%S'))

with tempfile.TemporaryDirectory(prefix='gnupg_', suffix=timestamp) as GNUPGHOME:

    c = gpg.Context(armor=True, offline=True, home_dir=GNUPGHOME)

    if args.filter != None:
        filter = args.filter
    else:
        input('\nEnter the filter you want to look for')

    f = open('var.tmp', 'w')
    f.write(f'export GNUPGHOME={GNUPGHOME}\nexport FILTER="{filter}"\nexport nodismount={args.no_dismount}')
    f.close()

    if args.quiet == False:
        print('Downloading gpg.conf')
    with suppress_stdout():
        wget.download('https://raw.githubusercontent.com/drduh/config/master/gpg.conf', GNUPGHOME, bar=None)

    if args.quiet == False:
        print('\n\nIt is now recommended that you DISABLE networking for the remainder of the process')
        input('Press ENTER to continue\n')

    if args.path == None and args.no_container == False:
        createVCcontainer()
        savedir = f'/media/veracrypt44/generated_keys{timestamp}/'
    elif args.path == None and args.no_container == True:
        savedir = f'{os.path.dirname(os.path.realpath(__file__))}/generated_keys{timestamp}/'
    elif args.path != None and os.path.isdir(args.path):
        savedir = f'{args.path}/generated_keys{timestamp}/'
    else:
        if args.quiet == False:
            print('Invalid path')
        sys.exit(1)
    os.mkdir(savedir)

    if args.name != None:
        realname = args.name
    else:
        realname = input('\nEnter your Name: ')

    if args.email == None:
        email = args.email
    else:
        email = input('Enter your Email: ')

    userid = realname + ' <' + email + '>'

    if args.stats:
        i = 0
        start = datetime.datetime.now()
        last = start

    while True:
        checkEntropy()
        dmkey = c.create_key(userid, algorithm='ed25519', expires=False, sign=args.signing_key, certify=True, force=True)
        fingerprint = format(dmkey.fpr)
        if args.stats:
            i += 1
            entropy = getEntropy()
            now = datetime.datetime.now()
            if (now - last) > datetime.timedelta(seconds=10):
                last = now
                print(f'Elapsed time: {str(now - start)} | Entropy: {str(entropy)} | Try #{str(i)}')
        if fingerprint[-len(filter):] == filter:
            break
        else:
            f = open('fp.tmp', 'w')
            f.write('export fingerprint=' + fingerprint)
            f.close()
            subprocess.run(
            r'''
                source fp.tmp
                source var.tmp
                gpg --batch --yes --delete-secret-and-public-keys ${fingerprint}
            '''
            , shell=True, check=True, executable='/bin/bash')
            os.remove(GNUPGHOME + '/openpgp-revocs.d/' + fingerprint + '.rev')

    if args.quiet == False:
        print('\nMATCH FOUND: ' + fingerprint)

    if args.stats:
        print(f'Elapsed time: {str(now - start)} | Entropy: {str(entropy)} | Try #{str(i)}')

    keyid = fingerprint[-16:]

    f = open(f'{savedir}publickey-0x{keyid}.asc', 'wb')
    f.write(c.key_export(pattern=fingerprint))
    f.close()

    f = open(f'{savedir}secretkey-0x{keyid}.key', 'wb')
    f.write(c.key_export_secret(pattern=fingerprint))
    f.close()
    os.chmod(f'{savedir}secretkey-0x{keyid}.key', 0o600)

    shutil.copytree(GNUPGHOME, savedir + os.path.basename(GNUPGHOME))
    if args.quiet == False:
        print('Securely erasing tmp files and unmounting encrypted container (unless otherwise indicated) ...')
    subprocess.run(
    r'''
        source var.tmp
        srm -r $GNUPGHOME || rm -rf $GNUPGHOME
        if [ nodismount == False ]; then
            veracrypt -d /media/veracrypt44 || echo 'Could not unmount container'
        fi
    '''
    , shell=True, check=True, executable='/bin/bash')

if args.quiet == False:
    print('If you are in an ephemeral environment, make sure to save the keys somewhere safe and recoverable!')

if os.path.isfile('fp.tmp'):
    os.remove('fp.tmp')
os.remove('var.tmp')

if args.quiet == False:
    print('\nExiting...\n')
sys.exit(0)
