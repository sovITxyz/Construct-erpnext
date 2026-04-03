# Copyright (c) 2026, Sovereign IT Services and contributors
# For license information, please see license.txt

import re

import frappe
from frappe import _
from frappe.utils import flt
from frappe.model.document import Document

_ACCOUNT_REF_PATTERN = re.compile(r"\{([^}]+)\}")


class FinancialRatio(Document):
	def validate(self):
		if not self.formula or not self.formula.strip():
			frappe.throw(_("Formula is required for a Financial Ratio"))

	def compute_ratio(self, period):
		"""Compute the ratio value for a given period string (e.g. '2026-01', '2026-Q1', '2026').

		Parses {Account Name} references in the formula, queries GL Entry balances,
		substitutes values, and evaluates the expression.
		"""
		if not self.formula:
			frappe.throw(_("Formula is empty, cannot compute ratio"))

		# Determine date range from period string
		fiscal_start, fiscal_end = _parse_period(period, self.company)

		# Find all account references
		account_refs = _ACCOUNT_REF_PATTERN.findall(self.formula)
		if not account_refs:
			frappe.throw(_("Formula must contain at least one {Account Name} reference"))

		# Query balances and build substitution map
		evaluated_formula = self.formula
		for account_name in account_refs:
			account_name_stripped = account_name.strip()

			# Verify account exists
			if not frappe.db.exists("Account", {"name": account_name_stripped, "company": self.company}):
				# Try matching by account_name field
				account_match = frappe.db.get_value(
					"Account",
					{"account_name": account_name_stripped, "company": self.company},
					"name",
				)
				if not account_match:
					frappe.throw(
						_("Account {0} not found for company {1}").format(
							account_name_stripped, self.company
						)
					)
				gl_account = account_match
			else:
				gl_account = account_name_stripped

			balance = flt(
				frappe.db.sql(
					"""
					SELECT SUM(debit) - SUM(credit)
					FROM `tabGL Entry`
					WHERE account = %s
						AND company = %s
						AND posting_date >= %s
						AND posting_date <= %s
						AND is_cancelled = 0
					""",
					(gl_account, self.company, fiscal_start, fiscal_end),
				)[0][0]
			)

			# Replace the {Account Name} token with the balance value
			evaluated_formula = evaluated_formula.replace(
				"{" + account_name + "}", str(balance)
			)

		# Safely evaluate the expression
		try:
			computed_value = flt(frappe.safe_eval(evaluated_formula))
		except Exception as e:
			frappe.throw(
				_("Error evaluating formula: {0}. Expanded formula: {1}").format(
					str(e), evaluated_formula
				)
			)

		benchmark = flt(self.benchmark_value)
		variance = computed_value - benchmark

		# Create result record
		result = frappe.new_doc("Financial Ratio Result")
		result.financial_ratio = self.name
		result.ratio_name = self.ratio_name
		result.period = period
		result.computed_value = computed_value
		result.benchmark_value = benchmark
		result.variance = variance
		result.company = self.company
		result.insert(ignore_permissions=True)

		return result


def _parse_period(period, company):
	"""Convert a period string to (start_date, end_date).

	Supports formats:
	  - 'YYYY-MM' for monthly
	  - 'YYYY-Q1' through 'YYYY-Q4' for quarterly
	  - 'YYYY' for annual
	"""
	import calendar
	from frappe.utils import getdate

	period = period.strip()

	# Monthly: YYYY-MM
	monthly_match = re.match(r"^(\d{4})-(\d{2})$", period)
	if monthly_match:
		year = int(monthly_match.group(1))
		month = int(monthly_match.group(2))
		last_day = calendar.monthrange(year, month)[1]
		return (
			getdate(f"{year}-{month:02d}-01"),
			getdate(f"{year}-{month:02d}-{last_day:02d}"),
		)

	# Quarterly: YYYY-Q1..Q4
	quarterly_match = re.match(r"^(\d{4})-Q([1-4])$", period)
	if quarterly_match:
		year = int(quarterly_match.group(1))
		quarter = int(quarterly_match.group(2))
		start_month = (quarter - 1) * 3 + 1
		end_month = start_month + 2
		last_day = calendar.monthrange(year, end_month)[1]
		return (
			getdate(f"{year}-{start_month:02d}-01"),
			getdate(f"{year}-{end_month:02d}-{last_day:02d}"),
		)

	# Annual: YYYY
	annual_match = re.match(r"^(\d{4})$", period)
	if annual_match:
		year = int(annual_match.group(1))
		return getdate(f"{year}-01-01"), getdate(f"{year}-12-31")

	frappe.throw(
		_("Invalid period format: {0}. Use YYYY-MM, YYYY-Q1..Q4, or YYYY").format(period)
	)


@frappe.whitelist()
def compute_ratio(ratio_name, period):
	"""Whitelist wrapper to compute a financial ratio from the client side."""
	if not ratio_name or not period:
		frappe.throw(_("Both ratio_name and period are required"))

	doc = frappe.get_doc("Financial Ratio", ratio_name)
	result = doc.compute_ratio(period)
	return result.as_dict()
