# Copyright 2021 Compassion CH (http://www.compassion.ch)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo.tests.common import TransactionCase


class TestMandrill(TransactionCase):
    def setUp(self):
        super().setUp()
        self.recipient = "to@example.com"
        self.mail, self.tracking_email = self.mail_send()
        self.mandrill_message_id = "0123456789abcdef0123456789abcdef"
        self.metadata = {
            "ip": "127.0.0.1",
            "user_agent": False,
            "os_family": False,
            "ua_family": False,
        }

        self.event_open = {
            "mandrill_events": [
                {
                    "ip": "111.111.111.111",
                    "ts": 1455189075,
                    "location": {
                        "country_short": "PT",
                        "city": "Porto",
                        "country": "Portugal",
                        "region": "Porto",
                        "longitude": -8.61098957062,
                        "postal_code": "-",
                        "latitude": 41.1496086121,
                        "timezone": "+01:00",
                    },
                    "msg": {
                        "sender": "username01@example.com",
                        "tags": [],
                        "smtp_events": [
                            {
                                "destination_ip": "222.222.222.222",
                                "diag": "250 2.0.0 ABCDEFGHIJK123456ABCDE mail "
                                "accepted for delivery",
                                "source_ip": "111.1.1.1",
                                "ts": 1455185877,
                                "type": "sent",
                                "size": 30276,
                            },
                        ],
                        "ts": 1455185876,
                        "clicks": [],
                        "metadata": {"tracking_email_id": f"{self.tracking_email.id}"},
                        "resends": [],
                        "state": "sent",
                        "_version": "abcdefghi123456ABCDEFG",
                        "template": None,
                        "_id": self.mandrill_message_id,
                        "email": "username02@example.com",
                        "opens": [
                            {
                                "ip": "111.111.111.111",
                                "ua": "Windows/Windows 7/Outlook 2010/Outlook 2010",
                                "ts": 1455186247,
                                "location": "Porto, PT",
                            },
                            {
                                "ip": "111.111.111.111",
                                "ua": "Windows/Windows 7/Outlook 2010/Outlook 2010",
                                "ts": 1455189075,
                                "location": "Porto, PT",
                            },
                        ],
                        "subject": "My favorite subject",
                    },
                    "_id": self.mandrill_message_id,
                    "user_agent_parsed": {
                        "ua_name": "Outlook 2010",
                        "mobile": False,
                        "ua_company_url": "http://www.microsoft.com/",
                        "os_icon": "http://cdn.mandrill.com/img/email-client-icons/"
                        "windows-7.png",
                        "os_company": "Microsoft Corporation.",
                        "ua_version": None,
                        "os_name": "Windows 7",
                        "ua_family": "Outlook 2010",
                        "os_url": "http://en.wikipedia.org/wiki/Windows_7",
                        "os_company_url": "http://www.microsoft.com/",
                        "ua_company": "Microsoft Corporation.",
                        "os_family": "Windows",
                        "type": "Email Client",
                        "ua_icon": "http://cdn.mandrill.com/img/email-client-icons/"
                        "outlook-2010.png",
                        "ua_url": "http://en.wikipedia.org/wiki/Microsoft_Outlook",
                    },
                    "event": "open",
                    "user_agent": "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.1; "
                    "Trident/7.0; SLCC2; .NET CLR 2.0.50727; "
                    ".NET CLR 3.5.30729; .NET CLR 3.0.30729; "
                    "Media Center PC 6.0; .NET4.0C; .NET4.0E; BRI/2; "
                    "Tablet PC 2.0; GWX:DOWNLOADED; "
                    "Microsoft Outlook 14.0.7166; ms-office; "
                    "MSOffice 14)",
                }
            ]
        }

        self.event_hard_bounce = {
            "mandrill_events": [
                {
                    "msg": {
                        "bounce_description": "bad_mailbox",
                        "sender": "username01@example.com",
                        "tags": [],
                        "diag": "smtp;550 5.4.1 [username02@example.com]: "
                        "Recipient address rejected: Access denied",
                        "smtp_events": [],
                        "ts": 1455194565,
                        "template": None,
                        "_version": "abcdefghi123456ABCDEFG",
                        "metadata": {"tracking_email_id": f"{self.tracking_email.id}"},
                        "resends": [],
                        "state": "bounced",
                        "bgtools_code": 10,
                        "_id": self.mandrill_message_id,
                        "email": "username02@example.com",
                        "subject": "My favorite subject",
                    },
                    "_id": self.mandrill_message_id,
                    "event": "hard_bounce",
                    "ts": 1455195340,
                }
            ]
        }

        self.event_soft_bounce = {
            "mandrill_events": [
                {
                    "msg": {
                        "bounce_description": "general",
                        "sender": "username01@example.com",
                        "tags": [],
                        "diag": "X-Notes; Error transferring to FQDN.EXAMPLE.COM\n ; "
                        "SMTP Protocol Returned a Permanent Error 550 5.7.1 "
                        "Unable to relay\n\n--==ABCDEFGHIJK12345678ABCDEFGH",
                        "smtp_events": [],
                        "ts": 1455194562,
                        "template": None,
                        "_version": "abcdefghi123456ABCDEFG",
                        "metadata": {"tracking_email_id": f"{self.tracking_email.id}"},
                        "resends": [],
                        "state": "soft-bounced",
                        "bgtools_code": 40,
                        "_id": self.mandrill_message_id,
                        "email": "username02@example.com",
                        "subject": "My favorite subject",
                    },
                    "_id": self.mandrill_message_id,
                    "event": "soft_bounce",
                    "ts": 1455195622,
                }
            ]
        }

        self.event_deferral = {
            "mandrill_events": [
                {
                    "msg": {
                        "sender": "username01@example.com",
                        "tags": [],
                        "smtp_events": [
                            {
                                "destination_ip": "123.123.123.123",
                                "diag": "Event description",
                                "source_ip": "145.145.145.145",
                                "ts": 1455192896,
                                "type": "deferred",
                                "size": 19513,
                            },
                        ],
                        "ts": 1455008558,
                        "clicks": [],
                        "resends": [],
                        "state": "deferred",
                        "_version": "1abcdefghijkABCDEFGHIJ",
                        "template": None,
                        "_id": self.mandrill_message_id,
                        "email": "username02@example.com",
                        "metadata": {"tracking_email_id": f"{self.tracking_email.id}"},
                        "opens": [],
                        "subject": "My favorite subject",
                    },
                    "diag": "454 4.7.1 <username02@example.com>: Relay access denied",
                    "_id": self.mandrill_message_id,
                    "event": "deferral",
                    "ts": 1455201028,
                }
            ]
        }

        self.event_reject = {
            "mandrill_events": [
                {
                    "msg": {
                        "_id": self.mandrill_message_id,
                        "subaccount": None,
                        "tags": [],
                        "smtp_events": [],
                        "ts": 1455194291,
                        "email": "username02@example.com",
                        "metadata": {"tracking_email_id": f"{self.tracking_email.id}"},
                        "state": "rejected",
                        "sender": "username01@example.com",
                        "template": None,
                        "reject": None,
                        "resends": [],
                        "clicks": [],
                        "opens": [],
                        "subject": "My favorite subject",
                    },
                    "_id": self.mandrill_message_id,
                    "event": "reject",
                    "ts": 1455194291,
                }
            ]
        }

        self.event_unsub = {
            "mandrill_events": [
                {
                    "msg": {
                        "_id": self.mandrill_message_id,
                        "subaccount": None,
                        "tags": [],
                        "smtp_events": [],
                        "ts": 1455194291,
                        "email": "username02@example.com",
                        "metadata": {"tracking_email_id": f"{self.tracking_email.id}"},
                        "state": "unsub",
                        "sender": "username01@example.com",
                        "template": None,
                        "reject": None,
                        "resends": [],
                        "clicks": [],
                        "opens": [],
                        "subject": "My favorite subject",
                    },
                    "_id": self.mandrill_message_id,
                    "event": "unsub",
                    "ts": 1455194291,
                }
            ]
        }

        self.event_spam = {
            "mandrill_events": [
                {
                    "msg": {
                        "sender": "username01@example.com",
                        "tags": [],
                        "smtp_events": [],
                        "ts": 1455186007,
                        "clicks": [],
                        "metadata": {"tracking_email_id": f"{self.tracking_email.id}"},
                        "resends": [],
                        "state": "spam",
                        "_version": "abcdefghi123456ABCDEFG",
                        "template": None,
                        "_id": self.mandrill_message_id,
                        "email": "username02@example.com",
                        "opens": [],
                        "subject": "My favorite subject",
                    },
                    "_id": self.mandrill_message_id,
                    "event": "spam",
                    "ts": 1455186366,
                }
            ]
        }

        self.event_click = {
            "mandrill_events": [
                {
                    "url": "http://www.example.com/index.php",
                    "ip": "111.111.111.111",
                    "ts": 1455186402,
                    "user_agent": "Mozilla/5.0 (Windows NT 6.1) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/48.0.2564.103 Safari/537.36",
                    "msg": {
                        "sender": "username01@example.com",
                        "tags": [],
                        "smtp_events": [
                            {
                                "destination_ip": "222.222.222.222",
                                "diag": "250 2.0.0 Ok: queued as 12345678",
                                "source_ip": "111.1.1.1",
                                "ts": 1455186065,
                                "type": "sent",
                                "size": 30994,
                            },
                        ],
                        "ts": 1455186063,
                        "clicks": [
                            {
                                "url": "http://www.example.com/index.php",
                                "ip": "111.111.111.111",
                                "ua": "Windows/Windows 7/Chrome/Chrome 48.0.2564.103",
                                "ts": 1455186402,
                                "location": "Madrid, ES",
                            },
                        ],
                        "metadata": {"tracking_email_id": f"{self.tracking_email.id}"},
                        "resends": [],
                        "state": "sent",
                        "_version": "abcdefghi123456ABCDEFG",
                        "template": None,
                        "_id": self.mandrill_message_id,
                        "email": "username02@example.com",
                        "opens": [
                            {
                                "ip": "111.111.111.111",
                                "ua": "Windows/Windows 7/Chrome/Chrome 48.0.2564.103",
                                "ts": 1455186402,
                                "location": "Madrid, ES",
                            },
                        ],
                        "subject": "My favorite subject",
                    },
                    "_id": self.mandrill_message_id,
                    "user_agent_parsed": {
                        "ua_name": "Chrome 48.0.2564.103",
                        "mobile": False,
                        "ua_company_url": "http://www.google.com/",
                        "os_icon": "http://cdn.mandrill.com/img/email-client-icons/"
                        "windows-7.png",
                        "os_company": "Microsoft Corporation.",
                        "ua_version": "48.0.2564.103",
                        "os_name": "Windows 7",
                        "ua_family": "Chrome",
                        "os_url": "http://en.wikipedia.org/wiki/Windows_7",
                        "os_company_url": "http://www.microsoft.com/",
                        "ua_company": "Google Inc.",
                        "os_family": "Windows",
                        "type": "Browser",
                        "ua_icon": "http://cdn.mandrill.com/img/email-client-icons/"
                        "chrome.png",
                        "ua_url": "http://www.google.com/chrome",
                    },
                    "event": "click",
                    "location": {
                        "country_short": "ES",
                        "city": "Madrid",
                        "country": "Spain",
                        "region": "Madrid",
                        "longitude": -3.70255994797,
                        "postal_code": "-",
                        "latitude": 40.4165000916,
                        "timezone": "+02:00",
                    },
                }
            ]
        }

    def mail_send(self):
        mail = self.env["mail.mail"].create(
            {
                "subject": "Test subject",
                "email_from": "from@example.com",
                "email_to": self.recipient,
                "body_html": "<p>This is a test message</p>",
            }
        )
        mail.send()
        # Search tracking created
        tracking_email = self.env["mail.tracking.email"].search(
            [
                ("mail_id", "=", mail.id),
            ]
        )
        return mail, tracking_email

    def test_process_hard_bounce_event(self):
        event_count_1 = self.env["mail.tracking.event"].search_count(
            [("tracking_email_id", "=", self.tracking_email.id)]
        )

        self.env["mail.tracking.email"].event_process(
            None, self.event_hard_bounce, self.metadata
        )

        event_count_2 = self.env["mail.tracking.event"].search_count(
            [("tracking_email_id", "=", self.tracking_email.id)]
        )

        self.assertGreater(event_count_2, event_count_1)
        self.assertEqual(
            self.tracking_email.tracking_event_ids[1].event_type, "hard_bounce"
        )

    def test_process_soft_bounce_event(self):
        event_count_1 = self.env["mail.tracking.event"].search_count(
            [("tracking_email_id", "=", self.tracking_email.id)]
        )

        self.env["mail.tracking.email"].event_process(
            None, self.event_soft_bounce, self.metadata
        )

        event_count_2 = self.env["mail.tracking.event"].search_count(
            [("tracking_email_id", "=", self.tracking_email.id)]
        )

        self.assertGreater(event_count_2, event_count_1)
        self.assertEqual(
            self.tracking_email.tracking_event_ids[1].event_type, "soft_bounce"
        )

    def test_process_deferral_event(self):
        event_count_1 = self.env["mail.tracking.event"].search_count(
            [("tracking_email_id", "=", self.tracking_email.id)]
        )

        self.env["mail.tracking.email"].event_process(
            None, self.event_deferral, self.metadata
        )

        event_count_2 = self.env["mail.tracking.event"].search_count(
            [("tracking_email_id", "=", self.tracking_email.id)]
        )

        self.assertGreater(event_count_2, event_count_1)
        self.assertEqual(
            self.tracking_email.tracking_event_ids[1].event_type, "deferral"
        )

    def test_process_reject_event(self):
        event_count_1 = self.env["mail.tracking.event"].search_count(
            [("tracking_email_id", "=", self.tracking_email.id)]
        )

        self.env["mail.tracking.email"].event_process(
            None, self.event_reject, self.metadata
        )

        event_count_2 = self.env["mail.tracking.event"].search_count(
            [("tracking_email_id", "=", self.tracking_email.id)]
        )

        self.assertGreater(event_count_2, event_count_1)
        self.assertEqual(self.tracking_email.tracking_event_ids[1].event_type, "reject")

    def test_process_unsub_event(self):
        event_count_1 = self.env["mail.tracking.event"].search_count(
            [("tracking_email_id", "=", self.tracking_email.id)]
        )

        self.env["mail.tracking.email"].event_process(
            None, self.event_unsub, self.metadata
        )

        event_count_2 = self.env["mail.tracking.event"].search_count(
            [("tracking_email_id", "=", self.tracking_email.id)]
        )

        self.assertGreater(event_count_2, event_count_1)
        self.assertEqual(self.tracking_email.tracking_event_ids[1].event_type, "unsub")

    def test_process_spam_event(self):
        event_count_1 = self.env["mail.tracking.event"].search_count(
            [("tracking_email_id", "=", self.tracking_email.id)]
        )

        self.env["mail.tracking.email"].event_process(
            None, self.event_spam, self.metadata
        )

        event_count_2 = self.env["mail.tracking.event"].search_count(
            [("tracking_email_id", "=", self.tracking_email.id)]
        )

        self.assertGreater(event_count_2, event_count_1)
        self.assertEqual(self.tracking_email.tracking_event_ids[1].event_type, "spam")

    def test_process_open_event(self):
        event_count_1 = self.env["mail.tracking.event"].search_count(
            [("tracking_email_id", "=", self.tracking_email.id)]
        )

        self.env["mail.tracking.email"].event_process(
            None, self.event_open, self.metadata
        )

        event_count_2 = self.env["mail.tracking.event"].search_count(
            [("tracking_email_id", "=", self.tracking_email.id)]
        )

        self.assertGreater(event_count_2, event_count_1)
        self.assertEqual(self.tracking_email.tracking_event_ids[1].event_type, "open")

    def test_process_click_event(self):
        event_count_1 = self.env["mail.tracking.event"].search_count(
            [("tracking_email_id", "=", self.tracking_email.id)]
        )

        self.env["mail.tracking.email"].event_process(
            None, self.event_click, self.metadata
        )

        event_count_2 = self.env["mail.tracking.event"].search_count(
            [("tracking_email_id", "=", self.tracking_email.id)]
        )

        self.assertGreater(event_count_2, event_count_1)
        self.assertEqual(self.tracking_email.tracking_event_ids[1].event_type, "click")
