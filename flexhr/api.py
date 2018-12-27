from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import date_diff, add_days, getdate
from erpnext.hr.doctype.employee.employee import is_holiday

# Shift Type - functions
def set_as_default(self,method):
    if self.is_default:
        frappe.db.sql("update `tabShift Type` set is_default=0 where name != %s",
        self.name)

# Attendance Request - functions
def validate_if_attendance_not_applicable_for_att_req(self,method):
        request_days = date_diff(self.to_date, self.from_date) + 1
        for number in range(request_days):
                attendance_date = add_days(self.from_date, number)
                skip_attendance = validate_if_holiday_or_leave(self,attendance_date)


def copy_fields_from_att_req_to_att(self,method):
        frappe.db.sql("""update `tabAttendance` set  
        checkin_time=%s,
        checkout_time=%s,
        duration=%s,
        shift_in_time=%s,
        shift_out_time=%s,
        shift_type=%s,
        early=%s,
        delay=%s,
        overtime=%s,
        review_remark='AR was system generated'
        where attendance_request = %s""",
        (self.checkin_time,
	self.checkout_time,
	self.duration,
	self.shift_in_time,
	self.shift_out_time,
	self.shift_type,
	self.early,
	self.delay,
	self.overtime,
        self.name))

def stop_delete_of_att_req(self,method):
        #frappe.throw(_("Cannot delete Attendance Request. Valid actions are submit or cancel"))
        pass

# Helper functions

def validate_if_holiday_or_leave(self,attendance_date) :
        # Check if attendance_date is a Holiday
        if is_holiday(self.employee, attendance_date):
                frappe.throw(_("Attendance not submitted for {0} as it is a Holiday.").format(attendance_date))
                return False

        # Check if employee on Leave
        leave_record = frappe.db.sql("""select half_day from `tabLeave Application`
                where employee = %s and %s between from_date and to_date
                and docstatus = 1""", (self.employee, attendance_date), as_dict=True)
        print 'leave_record'
        print leave_record
        if leave_record:
                frappe.throw(_("Attendance not submitted for {0} as {1} on leave.").format(attendance_date, self.employee))
                return False
         # There is no use allowing half day attendance, instead employee should go for half day leave if not done
        if self.half_day==1:
                frappe.throw(_("Attendance not submitted for half day. Instead put half day leave on {0}").format(attendance_date))
                return False
        return True


@frappe.whitelist()
def default_leave_type_for_lwp(doctype, txt, searchfield, start, page_len, filters):
        # return frappe.get_list('Leave Type', filters={'docstatus': 0, 'is_lwp': 1}, fields=['name'], order_by='modified')
        return frappe.db.sql("""select name from `tabLeave Type`
where 
docstatus=0 
and is_lwp=1""".format(**{
			'key': searchfield,
		}), {
			'txt': "%%%s%%" % txt,
			'_txt': txt.replace("%", ""),
			'start': start,
			'page_len': page_len
		})


####

@frappe.whitelist()
def is_holiday_on_half_date(employee, leave_type,half_day_date):
        if not frappe.db.get_value("Leave Type", leave_type, "include_holiday"):
                if is_holiday(employee,half_day_date):
                        return True
        else:
                return False
def get_number_of_leave_days(employee, leave_type, from_date, to_date, half_day = None, half_day_date = None):
	number_of_days = 0
	if cint(half_day) == 1:
		if from_date == to_date:
			number_of_days = 0.5
		else:
			number_of_days = date_diff(to_date, from_date) + .5
	else:
		number_of_days = date_diff(to_date, from_date) + 1

	if not frappe.db.get_value("Leave Type", leave_type, "include_holiday"):
		number_of_days = flt(number_of_days) - flt(get_holidays(employee, from_date, to_date))
	return number_of_days