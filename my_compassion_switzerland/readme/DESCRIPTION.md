This module provides functionalities specific to the "My Compassion" portal for Compassion Switzerland, focusing on volunteer engagement.

**Key Features:**

* **Volunteer Dashboard**: Adds a new portal page at `/my2/volunteering` to display all volunteering opportunities.
* **Rich Engagement Cards**: Extends the `advocate.engagement` model to support rich content (images, translatable labels, descriptions) for displaying opportunities on the website.
* **Prayer Subscription**: Allows users to subscribe to or unsubscribe from the 'Prayer' engagement directly from the dashboard with a single click.
* **Volunteer Registration Form**: Includes a comprehensive form for users to register their interest in volunteering. Submissions trigger a notification email to the appropriate department based on the user's language.
* **Portal Security**: Ensures that only engagement types explicitly marked as "Activate for My Compassion" are visible to portal users.
* **eBill Payment Option**: Injects an "eBill" payment method into the new-sponsorship wizard, backed by the PostFinance recipient-subscription workflow (`ebill_postfinance_recipient_subscription`).
* **Portal Grafts**: A "Translate a letter" button on the dashboard volunteering vignette for letter translators, a "Together" crowdfunding link in the account menu for campaign participants, and a "How to register?" guide link on the signup page.
* **Swiss Donation Catalog**: Seeds the fund and gift products (with images, impact statements and translations) shown on the MyCompassion giving pages.