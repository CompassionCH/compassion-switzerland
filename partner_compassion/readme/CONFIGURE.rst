Add the following parameters to your Odoo configuration file:

* ``smb_user`` : user for connecting on the NAS of Compassion with Samba
* ``smb_pwd`` : password for Samba
* ``smb_ip`` : IP address of the NAS of Compassion
* ``smb_port`` : Samba port of the NAS
* ``partner_data_password`` : The password for encrypted ZIP file containing erased partner history

Add the following system parameters in Odoo->Settings->System Parameters

* ``partner_compassion.share_on_nas`` : Name of the Samba root share
* ``partner_compassion.store_path`` : Path to the ZIP file containing erased partner history
