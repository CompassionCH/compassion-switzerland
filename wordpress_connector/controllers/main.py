# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import http
from odoo.http import request


class TestAppController(http.Controller):

    @http.route('/mobile-app', type='json', auth='public', methods=['POST'],
                csrf=False)
    def test_app(self):
        """
        Test controller to return some children to display in the mobile app
        :param number_children: number of children to search
        :param params: optional parameters
        :return: children data in list of dictionaries
        """
        content = request.jsonrequest
        global_pool = request.env[
            'compassion.childpool.search'].sudo().create({
                'take': content.get('number_children', 3),
            })
        global_pool.rich_mix()
        children = global_pool.global_child_ids
        return children.read([
            'name',
            'gender',
            'birthdate',
            'age',
            'image_url',
            'local_id',
            'waiting_days'
        ])
