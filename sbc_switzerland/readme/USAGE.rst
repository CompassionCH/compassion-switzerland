Used by the onramp_compassion module to send an email on reception of a new
child letter.

The letter is sent to the sponsor's email address, using a SendGrid email
template corresponding to the sponsor's language. Templates for every language
have to be registered in the TemplateList model after creating them on the
`SendGrid web interface <https://sendgrid.com/templates>`_.

The template should contain the following substitution variables which will be
replaced with corresponding values:

- ``{sponsor}`` Full name of the sponsor
- ``{child}`` First name of the child
- ``{letter_url}`` URL where the letter can be viewed/downloaded
