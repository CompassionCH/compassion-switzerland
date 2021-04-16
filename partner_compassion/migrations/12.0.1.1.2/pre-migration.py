def migrate(cr, version):
    if not version:
        return

    # Put other indexes to avoid unique constraint errors when updating data
    cr.execute("""
    UPDATE res_partner_segment
    SET segment_index = segment_index + 10
    """)
