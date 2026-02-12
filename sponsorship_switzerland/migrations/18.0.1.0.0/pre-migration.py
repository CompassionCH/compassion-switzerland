def migrate(cr, version):
    cr.execute("""
        DELETE FROM ir_model_data WHERE module = 'sponsorship_switzerland'
        AND model='product.pricelist.item';""")
