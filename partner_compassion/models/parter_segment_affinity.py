##############################################################################
#
#    Copyright (C) 2021 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Jonathan Guerne <jonathan.guerne@gmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import api, fields, models


class ResPartnerSegmentAffinity(models.Model):
    _name = "res.partner.segment.affinity"

    partner_id = fields.Many2one("res.partner", "Partner")
    segment_id = fields.Many2one("res.partner.segment", "Segment")

    affinity = fields.Integer(
        help='affinity of the partner for this segment (in percentage).')

    @api.model
    def create(self, vals):
        seg_affin_id = super(ResPartnerSegmentAffinity, self).create(vals)

        seg_affin_id.partner_id.all_segments = [(4, seg_affin_id.id)]
        return seg_affin_id

    @api.multi
    def unlink(self):
        for seg_affin in self:

            seg_affin.partner_id.all_segments = [(2, seg_affin.id)]
            super(ResPartnerSegmentAffinity, seg_affin).unlink()
        return True
