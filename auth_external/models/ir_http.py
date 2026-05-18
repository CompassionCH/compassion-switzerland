##############################################################################
#
#    Copyright (C) 2026 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#
#    The licence is in the file __manifest__.py
#
#    @author: Noé Berdoz <nberdoz@compassion.ch>
#
##############################################################################
# auth_external: ir.http override that stashes the request's
# Authorization header in thread-local storage before dispatch, so
# res.users.check / _check_credentials can read it during XMLRPC
# dispatch (where odoo.http.borrow_request() makes `request` unbound).
#
# Thread-local key: `auth_external_authorization` — namespaced to
# avoid collision with `uid` / `dbname` that Odoo already sets on the
# current thread.
##############################################################################
import threading

from odoo import models
from odoo.http import request


class IrHttp(models.AbstractModel):
    _inherit = "ir.http"

    @classmethod
    def _dispatch(cls, endpoint):
        thread = threading.current_thread()
        if request:
            thread.auth_external_authorization = request.httprequest.environ.get(
                "HTTP_AUTHORIZATION", ""
            )
        else:
            thread.auth_external_authorization = ""
        try:
            return super()._dispatch(endpoint)
        finally:
            # Clear to prevent cross-request leakage on reused worker
            # threads.
            thread.auth_external_authorization = ""
