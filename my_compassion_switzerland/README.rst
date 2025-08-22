=========================
My Compassion Switzerland
=========================


.. _Description:

Description
-----------
This module provides functionalities specific to the "My Compassion" portal for Compassion Switzerland, focusing on volunteer engagement.

**Key Features:**

* **Volunteer Dashboard**: Adds a new portal page at `/my2/volunteering` to display all volunteering opportunities.
* **Rich Engagement Cards**: Extends the `advocate.engagement` model to support rich content (images, translatable labels, descriptions) for displaying opportunities on the website.
* **Prayer Subscription**: Allows users to subscribe to or unsubscribe from the 'Prayer' engagement directly from the dashboard with a single click.
* **Volunteer Registration Form**: Includes a comprehensive form for users to register their interest in volunteering. Submissions trigger a notification email to the appropriate department based on the user's language.
* **Portal Security**: Ensures that only engagement types explicitly marked as "Activate for My Compassion" are visible to portal users.


.. _Use-Cases-/-Context:

Use Cases / Context
-------------------
The My Compassion Switzerland platform needed a centralized and engaging way for supporters to discover and participate in volunteering opportunities. Previously, this information was scattered, and the process for expressing interest was not streamlined.

This module was created to:
1.  Provide a single, user-friendly dashboard for all volunteering roles.
2.  Enable rich, visual content for each opportunity to increase engagement.
3.  Simplify the subscription process for recurring activities like the 'Prayer' letter.
4.  Standardize the registration process for new volunteers and ensure inquiries are routed to the correct internal teams.


.. _Configuration:

Configuration
-------------
To configure the volunteering opportunities displayed on the website:

1.  Navigate to the backend menu where **Advocate Engagements** are managed (Sponsorships/Advocates/Engagement types).
2.  Select an existing engagement (e.g., "Prayer") or create a new one.
3.  In the form view, go to the **My Compassion** tab.
4.  Check the box **Activate for MyCompassion**.
5.  Fill in the website-specific fields:
    * **Picture**: The main image for the volunteering card.
    * **Alt Text**: Accessibility text for the image.
    * **Label**: The title of the card.
    * **Description**: The text content of the card.
    * **External Link / Internal Link**: Define the behavior of the call-to-action button. An internal link is used for special actions like the prayer subscription, while an external link can point to another website for more information. If neither is set, the button will link to the registration form on the same page.


.. _Usage:

Usage
-----
Once configured, authenticated portal users can navigate to the `/my2/volunteering` page on the website. From there, they can:

* View the available volunteering opportunities.
* Subscribe to or unsubscribe from the Prayer letter.
* Fill out the registration form to express their interest in other volunteering roles.


.. _Contributors:

Contributors
------------
* Daniel Palumbo <dpalumbo@compassion.ch>
* Noé Berdoz <nberdoz@compassion.ch>


Authors
-------

* Daniel Palumbo

