import logging

from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)

# T3633: the letter import commits inside a queue job, which needs the option
# "Allow Commit" on the job function. The function is now declared in
# data/queue_job_data.xml. If it was already created by hand in the database, it
# has no XML id and the module update would create a second function next to it.
# We give it the XML id, so that the update sets the option on the existing one.

JOB_FUNCTION_NAME = "<import.letters.history>.run_analyze"
XMLID_MODULE = "sbc_switzerland"
XMLID_NAME = "job_function_import_letters_run_analyze"


@openupgrade.migrate()
def migrate(env, version):
    cr = env.cr
    cr.execute("SELECT to_regclass('queue_job_function')")
    if not cr.fetchone()[0]:
        # queue_job is installed with this update, nothing exists yet
        return
    cr.execute(
        "SELECT 1 FROM ir_model_data WHERE module = %s AND name = %s",
        (XMLID_MODULE, XMLID_NAME),
    )
    if cr.fetchone():
        return
    cr.execute(
        "SELECT id FROM queue_job_function WHERE name = %s ORDER BY id",
        (JOB_FUNCTION_NAME,),
    )
    function_ids = [row[0] for row in cr.fetchall()]
    if not function_ids:
        return
    if len(function_ids) > 1:
        _logger.warning(
            "Several job functions named %s (ids %s): only the first one is kept "
            "as the declared function, remove the others by hand.",
            JOB_FUNCTION_NAME,
            function_ids,
        )
    cr.execute(
        """
        INSERT INTO ir_model_data (module, name, model, res_id, noupdate)
        VALUES (%s, %s, 'queue.job.function', %s, false)
        """,
        (XMLID_MODULE, XMLID_NAME, function_ids[0]),
    )
    _logger.info(
        "Job function %s (id %s) now has the XML id %s.%s",
        JOB_FUNCTION_NAME,
        function_ids[0],
        XMLID_MODULE,
        XMLID_NAME,
    )
