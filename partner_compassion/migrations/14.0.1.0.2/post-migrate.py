from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE res_partner rp
        SET city_id = rc.id 
        FROM res_city rc
        WHERE rp.city = rc.name 
            AND rp.country_id = rc.country_id
            AND rp.state_id = rc.state_id
            AND rp.city_id IS NULL
            AND rp.parent_id IS NULL;
        """,
    )
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE res_partner rp 
        SET zip_id=rcz.id 
        FROM res_city_zip rcz
        WHERE rp.city_id = res_city_zip.city_id 
            AND rp.zip = rcz.name
            AND rp.zip_id IS NULL
            AND rp.parent_id IS NULL;
        """,
    )
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE res_partner rp 
        SET zip_id = rp_parent.zip_id, city_id = rp_parent.city_id
        FROM (
            SELECT zip_id, city_id 
            FROM res_partner) rp_parent
        WHERE rp.parent_id = rp_parent.id;
        """,
    )