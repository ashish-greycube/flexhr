import frappe
from frappe import _
from erpnext.hr.doctype.payroll_entry.payroll_entry import PayrollEntry
from frappe.utils import cint, flt, nowdate, add_days, getdate, fmt_money, add_to_date, DATE_FORMAT, date_diff

def get_sal_slip_list_with_employee(self, ss_status, as_dict=False):
    """
        Returns list of salary slips based on selected criteria
    """
    cond = self.get_filter_condition()

    ss_list = frappe.db.sql("""
        select t1.name, t1.salary_structure ,t1.employee,t1.employee_name
        from `tabSalary Slip` t1
        where t1.docstatus = %s and t1.start_date >= %s and t1.end_date <= %s
        and (t1.journal_entry is null or t1.journal_entry = "") and ifnull(salary_slip_based_on_timesheet,0) = %s %s
    """ % ('%s', '%s', '%s','%s', cond), (ss_status, self.start_date, self.end_date, self.salary_slip_based_on_timesheet), as_dict=as_dict)
    return ss_list

def get_salary_components_each_employee(self, component_type,ss_name):
    salary_components = frappe.db.sql("""select salary_component, amount, parentfield
        from `tabSalary Detail` where parentfield = %s and parent =%s""",
        (component_type,ss_name), as_dict=True)
    return salary_components

def get_salary_component_total_each_emp(self,ss_name, component_type = None):
    salary_components = get_salary_components_each_employee(self,component_type,ss_name)
    if salary_components:
        component_dict = {}
        for item in salary_components:
            add_component_to_accrual_jv_entry = True
            if component_type == "earnings":
                is_flexible_benefit, only_tax_impact = frappe.db.get_value("Salary Component", item['salary_component'], ['is_flexible_benefit', 'only_tax_impact'])
                if is_flexible_benefit == 1 and only_tax_impact ==1:
                    add_component_to_accrual_jv_entry = False
            if add_component_to_accrual_jv_entry:
                component_dict[item['salary_component']] = component_dict.get(item['salary_component'], 0) + item['amount']
        account_details = self.get_account(component_dict = component_dict)
        return account_details

def get_loan_details_each_emp(self,ss_name):
    """
        Get loan details from submitted salary slip based on selected criteria
    """
    cond = self.get_filter_condition()
    cond += " and t1.name = '" + ss_name.replace("'", "\'") + "'"
    return frappe.db.sql(""" select eld.loan_account, eld.loan,
            eld.interest_income_account, eld.principal_amount, eld.interest_amount, eld.total_payment
        from
            `tabSalary Slip` t1, `tabSalary Slip Loan` eld
        where
            t1.docstatus = 1 and t1.name = eld.parent and start_date >= %s and end_date <= %s %s
        """ % ('%s', '%s', cond), (self.start_date, self.end_date), as_dict=True) or []

def make_accrual_jv_entry(self):
    self.check_permission('write')
    salary_slips = get_sal_slip_list_with_employee(self,ss_status = 1, as_dict = True)
    if salary_slips:
        for ss in salary_slips:
            print('custome--custome-----custome------------------------make_accrual_jv_entry----------')
            print(ss.employee)
            employee_payroll_cost_center=None
            employee_payroll_cost_center=frappe.get_value('Employee', ss.employee, 'employee_payroll_cost_center')
            if employee_payroll_cost_center is None:
                employee_payroll_cost_center=self.cost_center
                if employee_payroll_cost_center is None:
                        employee_payroll_cost_center=frappe.get_cached_value('Company',{"company_name": self.company},  "cost_center")

            earnings = get_salary_component_total_each_emp(self,ss_name=ss.name,component_type = "earnings") or {}
            deductions = get_salary_component_total_each_emp(self,ss_name=ss.name,component_type = "deductions") or {}
            default_payroll_payable_account = self.get_default_payroll_payable_account()
            loan_details = get_loan_details_each_emp(self,ss_name=ss.name)
            jv_name = ""
            precision = frappe.get_precision("Journal Entry Account", "debit_in_account_currency")

            if earnings or deductions:
                journal_entry = frappe.new_doc('Journal Entry')
                journal_entry.voucher_type = 'Journal Entry'
                journal_entry.user_remark = _('Salary Payable Entry for Employee {0} : {1} for the period from  {2}  to {3}')\
                .format(ss.employee,ss.employee_name,self.start_date, self.end_date)
                journal_entry.company = self.company
                journal_entry.posting_date = self.posting_date
                journal_entry.remark=ss.name
                accounts = []
                payable_amount = 0

                # Earnings
                for acc, amount in earnings.items():
                    print acc
                    print ss.employee
                    party=ss.employee
                    print party
                    print '-----------------------'
                    payable_amount += flt(amount, precision)
                    accounts.append({
                            "account": acc,
                            "debit_in_account_currency": flt(amount, precision),
                            "cost_center": employee_payroll_cost_center,
                            "project": self.project,

                        })

                # Deductions
                for acc, amount in deductions.items():
                    payable_amount -= flt(amount, precision)
                    accounts.append({
                            "account": acc,
                            "credit_in_account_currency": flt(amount, precision),
                            "cost_center": employee_payroll_cost_center,
                            "project": self.project
                        })

                # Loan
                for data in loan_details:
                    accounts.append({
                            "account": data.loan_account,
                            "credit_in_account_currency": data.principal_amount
                        })

                    if data.interest_amount and not data.interest_income_account:
                        frappe.throw(_("Select interest income account in loan {0}").format(data.loan))

                    if data.interest_income_account and data.interest_amount:
                        accounts.append({
                            "account": data.interest_income_account,
                            "credit_in_account_currency": data.interest_amount,
                            "cost_center": employee_payroll_cost_center,
                            "project": self.project
                        })
                    payable_amount -= flt(data.total_payment, precision)

                # Payable amount
                accounts.append({
                    "account": default_payroll_payable_account,
                    "credit_in_account_currency": flt(payable_amount, precision),
                    "party_type":'Employee',
                    "party":party,
                    "cost_center": employee_payroll_cost_center,
                    "project": self.project
                })
                print accounts
                journal_entry.set("accounts", accounts)
                journal_entry.title = default_payroll_payable_account + '-'+str(party)
                journal_entry.save()
                print 'jjjjjjjjjjjjjjjjjjjj'
                print journal_entry.name
                print journal_entry.as_json()

                try:
                    journal_entry.submit()
                    jv_name = journal_entry.name
                    self.update_salary_slip_status(jv_name = jv_name)
                except Exception as e:
                    frappe.msgprint(e)

        return jv_name

def make_payment_entry(self):
    print('----------------inside custom------------------------------')
    self.check_permission('write')

    cond = self.get_filter_condition()
    salary_slip_name_list = frappe.db.sql(""" select t1.name,t1.employee,t1.employee_name from `tabSalary Slip` t1
        where t1.docstatus = 1 and start_date >= %s and end_date <= %s %s
        """ % ('%s', '%s', cond), (self.start_date, self.end_date), as_list = True)

    if salary_slip_name_list and len(salary_slip_name_list) > 0:
        salary_slip_total = 0
        for salary_slip_name in salary_slip_name_list:
            salary_slip = frappe.get_doc("Salary Slip", salary_slip_name[0])
            salary_slip_total=0
            for sal_detail in salary_slip.earnings:
                is_flexible_benefit, only_tax_impact, creat_separate_je, statistical_component = frappe.db.get_value("Salary Component", sal_detail.salary_component,
                    ['is_flexible_benefit', 'only_tax_impact', 'create_separate_payment_entry_against_benefit_claim', 'statistical_component'])
                if only_tax_impact != 1 and statistical_component != 1:
                    if is_flexible_benefit == 1 and creat_separate_je == 1:
                        self.create_journal_entry(sal_detail.amount, sal_detail.salary_component)
                    else:
                        salary_slip_total += sal_detail.amount
            for sal_detail in salary_slip.deductions:
                statistical_component = frappe.db.get_value("Salary Component", sal_detail.salary_component, 'statistical_component')
                if statistical_component != 1:
                    salary_slip_total -= sal_detail.amount
            if salary_slip_total > 0:
                create_journal_entry_each_emp(self,salary_slip_total, "salary",salary_slip_name[1])

def create_journal_entry_each_emp(self, je_payment_amount, user_remark,party):
    default_payroll_payable_account = self.get_default_payroll_payable_account()
    precision = frappe.get_precision("Journal Entry Account", "debit_in_account_currency")

    journal_entry = frappe.new_doc('Journal Entry')
    account_type=frappe.get_value('Account', self.payment_account, 'account_type')
    journal_entry.voucher_type = account_type+' Entry'
    journal_entry.user_remark = _('Payment of {0} for {1} from {2} to {3}')\
        .format(user_remark,party,self.start_date, self.end_date)
    journal_entry.company = self.company
    journal_entry.posting_date = self.posting_date

    payment_amount = flt(je_payment_amount, precision)

    employee_payroll_cost_center=frappe.get_value('Employee', party, 'employee_payroll_cost_center')
    if employee_payroll_cost_center is None:
        employee_payroll_cost_center=self.cost_center
        if employee_payroll_cost_center is None:
                employee_payroll_cost_center=frappe.get_cached_value('Company',{"company_name": self.company},  "cost_center")

    journal_entry.set("accounts", [
        {
            "account": self.payment_account,
            "credit_in_account_currency": payment_amount,
            "cost_center": employee_payroll_cost_center,
        },
        {
            "account": default_payroll_payable_account,
            "debit_in_account_currency": payment_amount,
            "party_type":'Employee',
            "party":party,
            "reference_type": self.doctype,
            "reference_name": self.name,
            "cost_center": employee_payroll_cost_center,
        }
    ])
    print journal_entry.as_json()
    journal_entry.save(ignore_permissions = True)

def create_custom_jv(self,method):
    # import types
    # self.make_accrual_jv_entry_1 = types.MethodType(make_accrual_jv_entry_1, self, PayrollEntry)
    print('-----------------module --custom----------------------------------------------------------------------------------')
    print(method)
    print('inside moduel..build my things----')
    PayrollEntry.make_accrual_jv_entry = make_accrual_jv_entry
    PayrollEntry.make_payment_entry = make_payment_entry