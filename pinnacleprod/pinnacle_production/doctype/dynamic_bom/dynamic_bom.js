// Copyright (c) 2025, OTPL and contributors
// For license information, please see license.txt

frappe.ui.form.on("Dynamic BOM", {
	refresh(frm) {},
	sales_order: function (frm) {
		if (frm.doc.sales_order) {
			frappe.db.get_doc("Sales Order", frm.doc.sales_order).then((doc) => {
				frm.set_value("finished_good", doc.items[0].item_code);
				frm.set_value("customer", doc.customer);
			});
		}
	},
});
