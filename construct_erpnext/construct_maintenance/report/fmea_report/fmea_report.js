// Copyright (c) 2026, SovIT and contributors
// For license information, please see license.txt

frappe.query_reports["FMEA Report"] = {
	filters: [
		{
			fieldname: "asset_category",
			label: __("Asset Category"),
			fieldtype: "Link",
			options: "Asset Category",
		},
		{
			fieldname: "min_rpn",
			label: __("Minimum RPN Score"),
			fieldtype: "Int",
		},
	],
};
