WARNING: You must install detectlanguage library on your server. It's used to
detect language from a text.
https://github.com/detectlanguage/detectlanguage-python

pip install detectlanguage

Add the following parameters to your Odoo configuration file:

* ``detect_language_api_key`` : api key for use detectlanguage library
* ``smb_user`` : user for connecting on the NAS of Compassion with Samba
* ``smb_pwd`` : password for Samba
* ``smb_ip`` : IP address of the NAS of Compassion
* ``smb_port`` : Samba port of the NAS
