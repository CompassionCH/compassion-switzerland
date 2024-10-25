# Running the tests
```sh
odoo/odoo-bin -c etc/dev_t1486.conf -u auth_external -i auth_external --test-tags=auth_external --stop-after-init
```

The tests should be run on an ***empty database with only this module installed*** (dependencies break these tests because of constraints on res_users/res_partners).