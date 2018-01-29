# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: David Coninckx <david@coninckx.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import logging

import sys
from datetime import datetime

from odoo import api, models, fields
from odoo.tools import relativedelta
from odoo.addons.child_compassion.models.compassion_hold import HoldType

from ..tools.wp_sync import WPSync


logger = logging.getLogger(__name__)


class CompassionChild(models.Model):
    _inherit = 'compassion.child'

    @api.multi
    def add_to_wordpress(self):
        # Solve the encoding problems on child's descriptions
        reload(sys)
        sys.setdefaultencoding('UTF8')

        in_two_years = datetime.today() + relativedelta(years=2)
        valid_children = self.filtered(
            lambda c: c.state == 'N' and c.desc_de and
            c.desc_fr and c.desc_it and
            c.project_id.description_fr and c.project_id.description_de and
            c.project_id.description_it and c.fullshot and
            (not c.completion_date or
             fields.Datetime.from_string(c.completion_date) > in_two_years)
        )

        error = self - valid_children
        if error:
            logger.error(
                "%s children have invalid data and were not pushed to "
                "wordpress." % str(len(error))
            )

        wp = WPSync()
        return wp.upload_children(valid_children)

    @api.multi
    def remove_from_wordpress(self):
        valid_children = self.filtered(lambda c: c.state == 'I')
        if valid_children:
            wp = WPSync()
            if wp.remove_children(valid_children):
                valid_children.write({'state': 'N'})
        return True

    @api.model
    def raz_wordpress(self):
        wp = WPSync()
        if wp.remove_all_children():
            children = self.search([('state', '=', 'I')])
            children.write({'state': 'N'})
        return True

    @api.multi
    def child_sponsored(self):
        """ Remove children from the website when they are sponsored. """
        to_remove_from_web = self.filtered(lambda c: c.state == 'I')
        if to_remove_from_web:
            to_remove_from_web.remove_from_wordpress()

        return super(CompassionChild, self).child_sponsored()

    @api.multi
    def child_released(self):
        """ Remove from typo3 when child is released """
        to_remove_from_web = self.filtered(lambda c: c.state == 'I')
        if to_remove_from_web:
            to_remove_from_web.remove_from_wordpress()

        return super(CompassionChild, self).child_released()

    @api.multi
    def child_departed(self):
        """ Remove from typo3 when child is deallocated """
        to_remove_from_web = self.filtered(lambda c: c.state == 'I')
        if to_remove_from_web:
            to_remove_from_web.remove_from_wordpress()

        return super(CompassionChild, self).child_departed()

    @api.model
    def refresh_wordpress_cron(self, take=120):
        """
        Find new children on the global childpool, put them on wordpress,
        remove old children and release the holds.
        :return: True
        """
        global_pool = self.env['compassion.childpool.search'].create({
            'take': take,
        })
        global_pool.rich_mix()
        hold_wizard = self.env['child.hold.wizard'].with_context(
            active_id=global_pool.id, async_mode=False
        ).create({
            'type': HoldType.CONSIGNMENT_HOLD.value,
            'expiration_date': self.env[
                'compassion.hold'].get_default_hold_expiration(
                HoldType.CONSIGNMENT_HOLD),
            'primary_owner': 1,
            'channel': 'web',
        })
        hold_wizard.onchange_type()
        res_action = hold_wizard.send()
        children = self.browse(res_action['domain'][0][2]).with_context(
            async_mode=False)
        for child in children:
            try:
                child.get_infos()
                child.mapped('project_id').update_informations()
            except:
                continue
        valid_children = children.filtered(
            lambda c: c.state == 'N' and c.desc_it and c.pictures_ids and
            c.project_id.description_it)
        old_children = self.search([
            ('state', '=', 'I'),
            ('hold_id.type', '!=', HoldType.NO_MONEY_HOLD.value)
        ])

        # Put children 5 by 5 to avoid delays
        def loop_five(n, max):
            while n < max:
                yield n
                n += 5
        try:
            with self.env.cr.savepoint():
                self.raz_wordpress()
                for i in loop_five(0, len(valid_children)):
                    try:
                        valid_children[i:i+5].add_to_wordpress()
                    except:
                        continue

                old_children.mapped('hold_id').release_hold()
        except:
            logger.error("Error when refreshing wordpress children.")

        return True
