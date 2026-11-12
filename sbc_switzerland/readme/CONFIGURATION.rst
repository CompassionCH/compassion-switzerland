Add the following parameters to your Odoo configuration file:

* ``sftp_user`` : user for connecting on the NAS of Compassion with Samba
* ``sftp_pwd`` : password for Samba
* ``sftp_ip`` : IP address of the NAS of Compassion
* ``sftp_port`` : Samba port of the NAS

Letter follow-up activities
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Three automation rules (Settings > Technical > Automation Rules) create a To-Do
activity:

* **Sponsorship: no child letter 3 months after start**: an active sponsorship
  has no letter from the child 3 months after its start date.
* **Sponsorship: no child letter 1 year after start**: the same, 1 year after
  the start date.
* **Letter: stuck in translation for 2 months**: a letter of an active
  sponsorship has stayed 2 months in "National Office Translation Queue",
  "To Translate" or "Translation check unsuccessful".

The rules are installed inactive. To use them, open each rule, set the
"Responsible" of its action, and activate the rule. Only dates that pass after
the module installation create activities; older cases are not flagged.
