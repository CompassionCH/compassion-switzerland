from datetime import datetime
import logging
from typing import Callable, List, Optional
from odoo import api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

class RefreshTokens(models.Model):
    """
    This model allows to store refresh tokens in the database for as long as they are not expired.
    This allows immediate revocation of refresh tokens as well as automatic reuse detection.
    """

    _name = "auth_external.refresh_tokens"

    jti = fields.Char(required=True)
    """
    JWT ID, used to lookup/identify a refresh token
    See https://www.rfc-editor.org/rfc/rfc7519#section-4.1.7
    """
    _sql_constraints = [
        (
            "jti_unique",
            "unique(jti)",
            "There cannot be duplicate tokens in RefreshTokens (jti must be unique)",
        )
    ]

    is_revoked = fields.Boolean(False)
    """
    Whether the refresh token is revoked. False by default (for newly generated
    tokens)
    """
    exp = fields.Datetime(required=True)
    """
    Expiration datetime of the token. Once this is in the past, a cron job can
    delete the token as it will not be accepted anymore by the authorization
    mechanism.
    """
    parent_id = fields.Many2one(
        "auth_external.refresh_tokens",
        string="Parent refresh_token",
        # if the parent token is deleted, this token becomes the root of the family
        ondelete="set null",
        index=True,
    )
    """
    Parent token of the current token. Declared as Many2one because odoo does
    not support One2one, but a token can only have a single parent (families of
    tokens are doubly linked lists)
    """
    child_id = fields.One2many(
        "auth_external.refresh_tokens", "parent_id", string="Child refresh_token"
    )
    """
    Child refresh_token. Should be One2one.
    """

    # TODO One2one constraints for parent_id and child_id

    @api.constrains("parent_id")
    def _check_hierarchy(self):
        if not self._check_recursion():
            raise models.ValidationError(
                "Error! You cannot create recursive refresh_token families."
            )

    @api.model
    def get_by_jti(self, jti: str) -> Optional["RefreshTokens"]:
        token = self.search([("jti", "=", jti)], limit=1)
        # is it possible to have a 1) non-expired and 2) inexistant token in the db
        if len(token) == 1:
            return token
        else:
            return None
        
    def link_child(self, child: "RefreshTokens") -> None:
        self.child_id = child
        child.parent_id = self


    def revoke(self) -> None:
        self.ensure_one()

        self.is_revoked = True

    def revoke_family(self) -> None:
        self.ensure_one()

        self.revoke()

        def revoke_list(
            start: "RefreshTokens",
            next: Callable[["RefreshTokens"], Optional["RefreshTokens"]],
        ) -> None:
            curr = start
            while len(curr) == 1:
                curr.revoke()
                curr = next(curr)

        # revoke parents
        revoke_list(self, lambda rt: rt.parent_id)
        # revoke children
        revoke_list(self, lambda rt: rt.child_id)

    def get_parents(self) -> List["RefreshTokens"]:
        self.ensure_one()

        parents = []
        curr = self
        while len(curr) == 1:
            curr = curr.parent_id
            parents.append(curr)
        parents.reverse() # to get family in right order from root
        return parents
    
    def get_children(self) -> List["RefreshTokens"]:
        self.ensure_one()
        children = []
        curr = self
        while len(curr) == 1:
            curr = curr.child_id
            children.append(curr)
        return children

    def get_family(self) -> List["RefreshTokens"]:
        return [*self.get_parents(), self, *self.get_children()]

    def family_str(self) -> str:
        self.ensure_one()

        family = self.get_family()
        out = ""
        for f in family:
            f_str = f"{f.id}:{'r' if f.is_revoked else 'v'}"
            if f.id == self.id:
                f_str = f"[{f_str}]"
            out += f"{f_str} <-> "
        return out

    @api.model
    def remove_expired_tokens(self):
        """
        Iterates of the refresh tokens and deletes all the records whose
        expiration date is in the past. Token expiration can still be checked by
        verifying the exp field of the JWT, so this operation is safe.
        """
        now = datetime.now()
        rts = self.sudo().search([])
        removed_rts = 0
        for rt in rts:
            if rt.exp <= now:
                rt.sudo().unlink()
                removed_rts += 1
        remaining_rts = len(self.sudo().search([]))
        _logger.info(f"RefreshTokens: removed {removed_rts} expired tokens, remains {remaining_rts} in the db.")
