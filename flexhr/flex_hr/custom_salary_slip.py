import frappe
from erpnext.hr.doctype.salary_slip.salary_slip import SalarySlip
from frappe import _
from frappe.utils import cint,flt, getdate, rounded
from erpnext import get_default_company

def sum_components(self, component_type, total_field, precision,amount_fhr_depends_on_absent):
    joining_date, relieving_date = frappe.db.get_value("Employee", self.employee,
        ["date_of_joining", "relieving_date"])

    if not relieving_date:
        relieving_date = getdate(self.end_date)

    if not joining_date:
        frappe.throw(_("Please set the Date Of Joining for employee {0}").format(frappe.bold(self.employee_name)))
    
    for d in self.get(component_type):
        # get value of fhr_depends_on_absent from _salary_structure_doc
        if not getattr(self, '_salary_structure_doc', None):
            self._salary_structure_doc = frappe.get_doc('Salary Structure', self.salary_structure)
        data = SalarySlip.get_data_for_eval(self)
        for key in ('earnings', 'deductions'):
            for struct_row in self._salary_structure_doc.get(key):
                if key=="earnings" and struct_row.fhr_depends_on_absent == 1:
                    fhr_depends_on_absent = cint(struct_row.fhr_depends_on_absent)

        if (self.salary_structure and
            cint(fhr_depends_on_absent) and
            (not
                self.salary_slip_based_on_timesheet or
                getdate(self.start_date) < joining_date or
                getdate(self.end_date) > relieving_date
            )):

            loss_amount = rounded(
                (flt(d.default_amount, precision) * flt(self.payment_days)
                / cint(self.total_working_days)), self.precision("amount", component_type)
            )
            amount_fhr_depends_on_absent=d.default_amount-loss_amount
    
    return amount_fhr_depends_on_absent

def calculate_lwp_net_pay(self):
    if self.salary_structure:
        self.calculate_component_amounts()
    precision = frappe.defaults.get_global_default("currency_precision")
    self.gross_pay = 0
    amount_fhr_depends_on_absent=0
    amount_fhr_depends_on_absent=sum_components(self,'earnings', 'gross_pay', precision,amount_fhr_depends_on_absent)
    return amount_fhr_depends_on_absent

def create_lwp_component(self,method):
    print('custom ss----------------------------------------------------')
    print(method)
    print('custom ss----------------------------------------------------')
    company = get_default_company()
    salary_component_absent=frappe.get_value('Company', company, 'fhr_absent_component')

    show_lwp_as_deduction=int(frappe.db.get_single_value("HR Settings", "show_lwp_as_deduction"))
    if show_lwp_as_deduction==1:
        if not (len(self.get("earnings")) or len(self.get("deductions"))):
            # get details from salary structure
            SalarySlip.get_emp_and_leave_details(self)
        else:
            SalarySlip.get_leave_details(self,lwp = self.leave_without_pay)

        amount_fhr_depends_on_absent=calculate_lwp_net_pay(self)
        if amount_fhr_depends_on_absent>0:
           # Cancel existing absent additional salary
            additional_salary_list = frappe.get_list("Additional Salary",{'employee': self.employee,'docstatus':1, 'salary_component': salary_component_absent,'payroll_date': ('between', [self.start_date, self.end_date])})
            print additional_salary_list
            if additional_salary_list:
                for additional_salary in additional_salary_list:
                    print additional_salary
                    attendance_obj = frappe.get_doc("Additional Salary", additional_salary['name'])
                    attendance_obj.cancel()            
            # create new additional salary
            ad_sal = frappe.new_doc("Additional Salary")
            ad_sal.employee=self.employee
            ad_sal.salary_component=salary_component_absent
            ad_sal.amount=amount_fhr_depends_on_absent
            ad_sal.payroll_date=self.start_date
            ad_sal.overwrite_salary_structure_amount=1
            ad_sal.save()
            ad_sal.submit()
    return