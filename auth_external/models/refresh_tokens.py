from typing import Optional
from odoo import api, fields, models
from odoo.exceptions import ValidationError

class RefreshTokens(models.Model):
    """
    This model allows to store refresh tokens in the database for as long as they are not expired.
    This allows immediate revocation of refresh tokens as well as automatic reuse detection.
    """

    _name = "auth_external.refresh_tokens"

    jti = fields.Char()
    """
    JWT ID, used to lookup a refresh token
    See https://www.rfc-editor.org/rfc/rfc7519#section-4.1.7
    """

    token = fields.Char()
    """
    String representation of the JWT refresh token
    TODO is this necessary given that we have jti ? 
    """
    is_revoked = fields.Boolean(False)
    """
    Whether the refresh token is revoked. False by default (for newly generated
    tokens)
    """
    expiration_datetime = fields.Datetime(required=True)
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

    # Enable special hierarchy support (speeds up lookup)
    # See https://www.odoo.com/documentation/14.0/developer/reference/addons/orm.html?highlight=fields%20many2many#odoo.models.BaseModel._parent_store
    _parent_store = True
    _parent_name = "parent_id" # optional if field is 'parent_id'
    parent_path = fields.Char(index=True)

    
    @api.constrains('parent_id') 
    def _check_hierarchy(self): 
        if not self._check_recursion(): 
            raise models.ValidationError( 
                'Error! You cannot create recursive refresh_token families.')
        
    def get_by_jti(self, jti: str) -> Optional["RefreshTokens"]:
        token = self.search([('jti', '=', jti)], limit=1)
        # is it possible to have a 1) non-expired and 2) inexistant token in the db
        if len(token) == 1:
            return token
        else:
            return None


    def revoke(self) -> None:
        self.ensure_one()

        self.is_revoked = True

    # TODO
    # def revoke_family(self) -> None:
    #     self.ensure_one()

    #     self.revoke_parents()
    #     self.revoke_children()

    # TODO : Cron to 
