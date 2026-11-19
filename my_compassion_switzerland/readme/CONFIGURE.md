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

To enable the eBill option in the new-sponsorship wizard:

1.  Configure the PostFinance eBill service (see `ebill_postfinance_recipient_subscription`: service credentials and the biller identifier system parameter).
2.  Publish the **eBill** payment mode (Invoicing/Configuration/Management/Payment Modes): the wizard only lists published payment modes, so publishing is the go-live switch.