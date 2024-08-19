from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE recurring_contract
        SET sub_proposal_date = (sub_proposal_date + 14);
        """
    )