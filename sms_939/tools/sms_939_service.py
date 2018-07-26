# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from io import BytesIO
from werkzeug.wrappers import Response


try:
    import xml.etree.cElementTree as etree
except ImportError:
    import xml.etree.ElementTree as etree


def _sanitize_message(message):
    return message.replace('&amp;', '&')\
        .replace('&', '&amp;')\
        .replace('<', '&lt;')\
        .replace('>', '&gt;')\
        .replace('\'', '&#39;')\
        .replace('"', '&quot;')


class SmsNotificationAnswer(object):
    def __init__(self, messages, costs=None, maxSMSsize=0):
        """
        :param messages: list of text messages to return to the sender
        :param costs: optional list of costs of the text messages
        :param maxSMSsize: optional maximal amount of split messages
        """
        if messages is None or not isinstance(messages, (list, basestring)):
            raise ValueError("You must give at least one message")
        if isinstance(messages, basestring):
            messages = [messages]
        if costs is not None and not isinstance(costs, list):
            costs = [costs]
        if costs is not None and len(costs) != len(messages):
            raise ValueError("Costs must be defined for each message sent.")
        self.messages = messages
        self.costs = costs
        self.maxSMSsize = maxSMSsize
        self.xml_message = self._get_xml()

    def __str__(self):
        return self.xml_message

    def _get_xml(self):
        # Generates XML Formatted message for 939 service
        document = etree.Element('NotificationReply')
        for index, message in enumerate(self.messages):
            mess_node = etree.SubElement(document, 'message')
            etree.SubElement(mess_node, 'text').text = _sanitize_message(
                message)
            if self.costs:
                etree.SubElement(mess_node, 'cost').text = str(
                    self.costs[index])
            if self.maxSMSsize:
                etree.SubElement(mess_node, 'maximumSMSAmount').text = str(
                    self.maxSMSsize)

        xml_buffer = BytesIO()
        et = etree.ElementTree(document)
        et.write(xml_buffer, encoding='utf-8', xml_declaration=True)
        return xml_buffer.getvalue()

    def get_answer(self):
        """
        Wraps messages in an XML Response compatible with 939 API.
        :return: werkzeug.Response object
        """
        return Response(self.xml_message, content_type='text/xml')
