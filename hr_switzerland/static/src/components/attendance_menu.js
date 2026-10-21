import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { ActivityMenu } from "@hr_attendance/components/attendance_menu/attendance_menu";

patch(ActivityMenu.prototype, {
  setup() {
    super.setup(...arguments);
    this.actionService = useService("action");
  },

  openMyAttendances() {
    this.dropdown.close();
    this.actionService.doAction("hr_switzerland.hr_attendance_my_action");
  },
});
