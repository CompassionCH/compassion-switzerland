import logging

import requests

_logger = logging.getLogger(__name__)


def serialize_date(date_obj):
    """Convertit un objet date/datetime en chaîne ISO 8601."""
    if date_obj and hasattr(date_obj, "isoformat"):
        return date_obj.isoformat()
    return str(date_obj) if date_obj else None


class WPSync(object):
    def __init__(self, wp_config):
        """
        wp_config should be defined :
         - host
         - user
         - password
        """
        self.wp_config = wp_config
        self.base_url = "https://{}/wp-json/child-import/v1/".format(wp_config.host)
        self.jwt_url = "https://{}/wp-json/jwt-auth/v1/".format(wp_config.host)
        self.token = None
        self.authenticate()

    def authenticate(self):
        """Get JWT token for auth."""
        try:
            url = self.jwt_url + "token"
            payload = {
                "username": self.wp_config.user,
                "password": self.wp_config.password,
            }
            headers = {"Content-Type": "application/json", "Accept": "application/json"}
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            self.token = data.get("token")
            if not self.token:
                raise Exception("No token found in the response : {}".format(data))
            _logger.info("JWT received.")
        except Exception as e:
            _logger.error(
                "JWT Auth Failure : %s\nResponse: %s",
                e,
                response.text if response is not None else "No response",
                exc_info=True,
            )
            raise

    def get_headers(self):
        """Prepare headers with token JWT."""
        if not self.token:
            self.authenticate()
        return {
            "Authorization": "Bearer " + self.token,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def upload_children(self, children):
        """Push children to Wordpress website.

        1 - Create dictionary and send to Wordpress (REST API)
        2 - Image URL (from Cloudinary) is now part of the post insert and
        not uploaded as file anymore

        :param children: compassion.child recordset
        :return: result of call to wordpress (true/false)
        """
        count_insert = 0
        for index, child in enumerate(children, start=1):
            _logger.info("Pushing child %s/%s", index, len(children))
            try:
                with children.env.cr.savepoint():
                    child_values = {
                        "local_id": child.local_id,
                        "number": child.local_id,
                        "first_name": child.preferred_name,
                        "name": child.name,
                        "full_name": child.name,
                        "birthday": serialize_date(child.birthdate),
                        "gender": child.gender,
                        "start_date": serialize_date(
                            child.unsponsored_since or child.date
                        ),
                        "desc": child.description_fr or "test",
                        "desc_de": child.description_de or "test",
                        "desc_it": child.description_it or "test",
                        "country": child.project_id.country_id.name,
                        "project": child.project_id.description_fr,
                        "project_de": child.project_id.description_de,
                        "project_it": child.project_id.description_it,
                        "cloudinary_url": child.image_url,
                    }
                    payload = {"child": child_values}
                    response = requests.post(
                        self.base_url + "add-child",
                        json=payload,
                        headers=self.get_headers(),
                    )
                    response.raise_for_status()
                    resp_data = response.json()
                    if resp_data.get("success") is True:
                        count_insert += 1
                        child.state = "I"
            except Exception:
                _logger.error("Child Upload failed", exc_info=True)

        if count_insert == len(children):
            _logger.info(
                f"Child Upload on Wordpress finished: {count_insert} children "
                "imported "
            )
        elif (count_insert > 0) and (count_insert < len(children)):
            _logger.warning(
                "Child Upload partially failed."
                + str(count_insert)
                + " of "
                + str(len(children))
            )
        else:
            _logger.error("Child Upload failed.")

        return count_insert

    def remove_children(self, children):
        try:
            payload = {"children": children.mapped("local_id")}
            response = requests.delete(
                self.base_url + "delete-children",
                json=payload,
                headers=self.get_headers(),
                verify=True,
            )
            response.raise_for_status()
            res_data = response.json()
            _logger.info("Remove from Wordpress : " + str(res_data))
            return res_data
        except Exception:
            _logger.error("Remove from WordPress failed", exc_info=True)
            return False

    def remove_all_children(self):
        try:
            response = requests.delete(
                self.base_url + "delete-all-children",
                headers=self.get_headers(),
                verify=True,
            )
            response.raise_for_status()
            res_data = response.json()
            _logger.info("Removed all children from Wordpress : " + str(res_data))
            return res_data
        except Exception:
            _logger.error("Remove all children from WordPress failed", exc_info=True)
            return False
