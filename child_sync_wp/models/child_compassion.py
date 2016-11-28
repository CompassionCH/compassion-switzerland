# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: David Coninckx <david@coninckx.com>
#
#    The licence is in the file __openerp__.py
#
##############################################################################
import logging

import sys

from openerp import api, models, _
from openerp.exceptions import Warning

from ..tools.wp_sync import WPSync


logger = logging.getLogger(__name__)


class CompassionChild(models.Model):
    _inherit = 'compassion.child'

    def child_add_to_wordpress(self):

        # Solve the encoding problems on child's descriptions
        reload(sys)
        sys.setdefaultencoding('UTF8')

        valid_children = self.filtered(lambda c: c.state == 'N')

        for child in valid_children:
            # Check for descriptions
            if not (child.desc_de and child.desc_fr and child.desc_it):
                raise Warning(
                    _('Missing descriptions for child %s') % child.local_id)
            if not (child.project_id.description_fr and
                    child.project_id.description_de and
                    child.project_id.description_it):
                raise Warning(
                    _('Missing descriptions for project %s') %
                    child.project_id.icp_id)

            # Check for pictures
            if not child.fullshot:
                self.env['compassion.child.pictures'].create({
                    'child_id': child.id})
                child = self.browse(child.id)
                if not child.fullshot:
                    raise Warning(
                        _('Child %s has no picture') % child.local_id)

        wp = WPSync()
        res = wp.upload_children(valid_children)
        if res:
            valid_children.write({'state': 'I'})
        return res

    def child_remove_from_wordpress(self):
        valid_children = self.filtered(lambda c: c.state == 'I')
        if valid_children:
            wp = WPSync()
            if wp.remove_children(valid_children):
                valid_children.write({'state': 'N'})
        return True

    @api.multi
    def child_sponsored(self):
        """ Remove children from the website when they are sponsored. """
        to_remove_from_web = self.filtered(lambda c: c.state == 'I')
        if to_remove_from_web:
            to_remove_from_web.child_remove_from_wordpress()

        return super(CompassionChild, self).child_sponsored()

    @api.multi
    def child_released(self):
        """ Remove from typo3 when child is released """
        to_remove_from_web = self.filtered(lambda c: c.state == 'I')
        if to_remove_from_web:
            to_remove_from_web.child_remove_from_wordpress()

        return super(CompassionChild, self).child_released()

    @api.multi
    def child_departed(self):
        """ Remove from typo3 when child is deallocated """
        to_remove_from_web = self.filtered(lambda c: c.state == 'I')
        if to_remove_from_web:
            to_remove_from_web.child_remove_from_wordpress()

        return super(CompassionChild, self).child_departed()
