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
# Authorization header in thread-local storage before dispatch.
#
# Why: v18's `dispatch_rpc` wraps the dispatch in `borrow_request()`,
# which POPS the request from the local stack. That means during
# `security.check` → `res.users.check` for an XMLRPC call, `request`
# is unbound and the Authorization header is inaccessible. v14 did
# not have this wrapper, so the v14 module read the header straight
# from `request.httprequest.headers`.
#
# The fix: read the header at ir.http._dispatch (where request is
# still bound), stash it in `threading.current_thread()`. Our
# `res.users.check` then reads it from the thread-local instead of
# from the (potentially unbound) request.
#
# Thread-local key: `auth_external_authorization` (any non-Odoo-core
# name avoids collision with `uid` / `dbname` already set by Odoo).
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
            thread.auth_external_authorization = (
                request.httprequest.environ.get("HTTP_AUTHORIZATION", "")
            )
        else:
            thread.auth_external_authorization = ""
        try:
            return super()._dispatch(endpoint)
        finally:
            # Always clear to prevent cross-request leakage when a
            # worker thread is reused.
            thread.auth_external_authorization = ""
