##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import logging

from xmlrpc.client import ServerProxy, SafeTransport, GzipDecodedResponse

_logger = logging.getLogger(__name__)


# Solves XMLRPC Parse response problems by stripping response
class CustomTransport(SafeTransport):
    def parse_response(self, response):
        # read response data from httpresponse, and parse it

        # Check for new http response object, else it is a file object
        if hasattr(response, 'getheader'):
            if response.getheader("Content-Encoding", "") == "gzip":
                stream = GzipDecodedResponse(response)
            else:
                stream = response
        else:
            stream = response

        p, u = self.getparser()

        while 1:
            data = stream.read(1024)
            data = data.strip()
            if not data:
                break
            if self.verbose:
                _logger.info("body:", repr(data))
            p.feed(data)

        if stream is not response:
            stream.close()
        p.close()

        return u.close()


class WPSync(object):

    def __init__(self, wp_config):
        self.xmlrpc_server = ServerProxy(
            'https://' + wp_config.host + '/xmlrpc.php',
            transport=CustomTransport())
        self.user = wp_config.user
        self.pwd = wp_config.password

    def test_xmlrpc(self):
        return self.xmlrpc_server.demo.sayHello()

    def upload_children(self, children):
        """ Push children to Wordpress website.

        1 - Create dictionary and send to Wordpress through XMLRPC method
        2 - Image URL (from Cloudinary) is now part of the post insert and
        not uploaded as file anymore

        :param children: compassion.child recordset
        :return: result of xmlrpc call to wordpress (true/false)
        """
        count_insert = 0

        try:
            for child in children:
                child_values = {
                    'local_id': child.local_id,
                    'number': child.local_id,
                    'first_name': child.preferred_name,
                    'name': child.name,
                    'full_name': child.name,
                    'birthday': child.birthdate,
                    'gender': child.gender,
                    # CO-1003 in case child has no unsponsored_since date,
                    # we use allocation date
                    'start_date': child.unsponsored_since or child.date,
                    'desc': child.desc_fr,
                    'desc_de': child.desc_de,
                    'desc_it': child.desc_it,
                    'country': child.project_id.country_id.name,
                    'project': child.project_id.description_fr,
                    'project_de': child.project_id.description_de,
                    'project_it': child.project_id.description_it,
                    'cloudinary_url': child.image_url
                }
                if self.xmlrpc_server.child_import.addChild(
                        self.user, self.pwd, child_values):
                    count_insert += 1
                    child.state = "I"

            if count_insert == len(children):
                _logger.info(
                    f"Child Upload on Wordpress finished: {count_insert} children "
                    "imported ")
                return count_insert
            else:
                if (count_insert > 0) and (count_insert < len(children)):
                    _logger.error("Child Upload partially failed." +
                                  str(count_insert) + " of " + len(children))
                else:
                    _logger.error("Child Upload failed." + str(count_insert))
        except Exception as error:
            _logger.error("Child Upload failed: " + error.message)

        return count_insert

    def remove_children(self, children):
        try:
            res = self.xmlrpc_server.child_import.deleteChildren(
                self.user, self.pwd, children.mapped('local_id'))
            _logger.info("Remove from Wordpress : " + str(res))
            return res
        except:
            _logger.error("Remove from Wordpress failed.")

        return False

    def remove_all_children(self):
        res = self.xmlrpc_server.child_import.deleteAllChildren(
            self.user, self.pwd)
        _logger.info("Remove from Wordpress : " + str(res))
        return res
