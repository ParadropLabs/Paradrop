import os
import crypt
import random

from paradrop.base import settings
from paradrop.lib.utils import pdos

class PasswordManager(object):
    def __init__(self):
        self.password_file = os.path.join(settings.CONFIG_HOME_DIR, 'password')

        # Try to parse the password file
        # self.records will have the pairs of user name and password hash
        parsed = False
        if pdos.exists(self.password_file):
            lines = pdos.readFile(self.password_file)
            if lines:
                for line in lines:
                    elements = line.split(':')
                    if len(elements) == 2:
                        self.records = []
                        self.records.append({
                            'user_name': elements[0],
                            'password_hash': elements[1]
                        })
                if len(lines) == len(self.records):
                    parsed = True
                else:
                    self.records = []

        if not parsed:
            self.reset()

    def _sync_password_file(self):
        file_content = ''
        for record in self.records:
            file_content = file_content + record['user_name'] + ':' + record['password_hash'] + '\n'

        pdos.write(self.password_file, file_content)

    def _generate_salt(self):
        # The salt can be generated with crypt.mksalt() on Python 3
        CHARACTERS = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
        salt = ''.join(random.choice(CHARACTERS) for i in range(16))
        # Use SHA512
        return '$6$' + salt

    def _retrieve_salt(self, password_hash):
        # Example hashed password
        # python -c 'import crypt; print crypt.crypt("", "$6$cMLi2vqIIJtq1Shm")'
        # $6$cMLi2vqIIJtq1Shm$41Ko1W2aTapn.p12G2dWRrRdStI2CrkC1JsftC/bPmwVgiy0vAQIXuuZEbVenyqsM6vZOsuzFrKrQC9NGd6/p.
        elements = password_hash.split('$')

        if len(elements) != 4:
            return None
        else:
            # Use SHA512
            return '$6$' + elements[2]

    def _hash_password(self, password):
        salt = self._generate_salt()
        return crypt.crypt(password, salt)

    def reset(self):
        self.records = []
        self.records.append({
            'user_name': settings.DEFAULT_PANEL_USERNAME,
            'password_hash': self._hash_password(settings.DEFAULT_PANEL_PASSWORD)
        })

        self._sync_password_file()

    def add_user(self, user_name, password):
        found_records = filter(lambda x: x['user_name'] == user_name, self.records)
        count = len(found_records)

        if count == 0:
            self.records.append({
                'user_name': user_name,
                'password_hash': self._hash_password(password)
            })
            self._sync_password_file()
            return True
        else:
            return False

    def remove_user(self, user_name):
        origin_len = len(self.records)
        self.records = [x for x in self.records if x['user_name'] != user_name]

        if len(self.records) != origin_len:
            self._sync_password_file()

    def verify_password(self, user_name, password):
        found_records = filter(lambda x: x['user_name'] == user_name, self.records)
        count = len(found_records)
        if count == 0:
            return False
        elif count == 1:
            password_hash = found_records[0]['password_hash']
            return crypt.crypt(password, self._retrieve_salt(password_hash)) == password_hash
        elif count > 1:
            # Should not be here
            raise Exception('Faint! Is there something wrong?')

    # We need to verify the user with the old password first
    def change_password(self, user_name, newPassword):
        if not user_name:
            user_name = settings.DEFAULT_PANEL_USERNAME

        for i in self.records:
            if i['user_name'] == user_name:
                i['password_hash'] = self._hash_password(newPassword)
                self._sync_password_file()
                return True

        # Could not found the user_name
        return False
