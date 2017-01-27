# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Philippe Heer
#
#    The licence is in the file __openerp__.py
#
##############################################################################
from openerp import api, models


class ExtendedReport(models.Model):
    _inherit = 'report'

    def _generate_christmas_bvr(self, cr, uid, ids,
                                report_name,
                                context=None):
        slip_model = self.pool['l10n_ch.payment_slip']
        partners = self.pool['res.partner'].browse(
            cr, uid, ids, context=context)
        return slip_model.draw_christmas(
            cr, uid,
            partners,
            a4=False,
            b64=False,
            report_name=report_name,
            out_format='PDF',
            context=context)

    @api.v7
    def get_pdf(self, cr, uid, ids, report_name, html=None, data=None,
                context=None):
        if report_name == 'christmas_bvr':
            return self._generate_christmas_bvr(
                cr,
                uid,
                ids,
                context=context,
                report_name=report_name,
            )
        else:
            return super(ExtendedReport, self).get_pdf(
                cr,
                uid,
                ids,
                report_name,
                html=html,
                data=data,
                context=context
            )

    @api.v8     # NOQA
    def get_pdf(self, records, report_name, html=None, data=None):
        return self._model.get_pdf(self._cr, self._uid,
                                   records.ids, report_name,
                                   html=html, data=data, context=self._context)
