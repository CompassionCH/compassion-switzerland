##############################################################################
#
#    Copyright (C) 2021 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Jonathan Guerne <jonathan.guerne@gmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import fields, models


class ResPartnerSegment(models.Model):
    _name = "res.partner.segment"
    _description = "Partner Segmentation"

    segment_index = fields.Integer(string='Segment Index used for segment computation by segmentation engine')
    name = fields.Char(string='Name')
    main_driver = fields.Char(string='Main driver', help='short description of the segment')

    segment_size = fields.Integer(
        help='number of partners for whom this is the primary segment',
        compute='_compute_segment_size'
    )

    segment_total = fields.Integer(
        help='percentage of categorized partners for whom this is the primary segment',
        compute='_compute_segment_total'
    )

    survey_result = fields.Html()
    image = fields.Binary(help='segment illustration')

    primary_partners = fields.One2many('res.partner', compute='_compute_primary_partners')
    secondary_partners = fields.One2many('res.partner', compute='_compute_secondary_partners')

    def _compute_segment_size(self):
        for segment in self:
            segment.segment_size = self.env['res.partner'].search_count([('primary_segment_id', '=', segment.id)])

    def _compute_segment_total(self):
        for segment in self:
            all_segmented_partners = self.env['res.partner'].search_count([('primary_segment_id', '!=', False)])
            segment.segment_total = round(segment.segment_size / all_segmented_partners,
                                          3) * 100 if all_segmented_partners > 0 else 0

    def _compute_primary_partners(self):
        for segment in self:
            segment.primary_partners = segment.env['res.partner'].search([('primary_segment_id', '=', segment.id)])

    def _compute_secondary_partners(self):
        for segment in self:
            segment.secondary_partners = segment.env['res.partner'].search([('secondary_segment_id', '=', segment.id)])
