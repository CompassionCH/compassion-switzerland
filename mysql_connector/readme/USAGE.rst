You can use this module directly from code:

* from mysql_connector.model.mysql_connector import mysql_connector
* con = mysql_connector()
* res_query = mysql_connector.select_all(sql, args)
* mysql_connector.upsert(table, vals)

See file mysql_connector.py for all supported methods. You can as well
inherit to expand the functionalities.
