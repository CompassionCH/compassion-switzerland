from openupgradelib import openupgrade


def copy_attachments(env, model_name):
    for record in env[model_name].search([]):
        attachment = env["ir.attachment"].search(
            [
                ("res_model", "=", model_name),
                ("res_id", "=", record.id),
                ("res_field", "=", "image"),
            ]
        )
        if attachment:
            for image_size in [
                "image_1920",
                "image_1024",
                "image_512",
                "image_256",
                "image_128",
            ]:
                attachment.copy({"res_field": image_size})


@openupgrade.migrate()
def migrate(env, version):
    copy_attachments(env, "hr.employee")
    copy_attachments(env, "product.template")
