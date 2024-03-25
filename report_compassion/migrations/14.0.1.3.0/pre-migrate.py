def migrate(cr, version):
    cr.execute(
        """
        SELECT res_id
        FROM ir_model_data
        WHERE module = 'report_compassion' AND model = 'report.paperformat'
    """
    )
    del_paperformat_ids = [r[0] for r in cr.fetchall()]
    cr.execute(
        """
        DELETE FROM  report_paperformat_parameter WHERE paperformat_id = ANY(%s)
    """,
        (del_paperformat_ids,),
    )
