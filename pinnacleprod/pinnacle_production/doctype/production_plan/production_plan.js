frappe.ui.form.on("Production Plan", {
	refresh(frm) {
		if (frm.doc.docstatus === 0) {
			frm.add_custom_button(__("Check Feasibility"), () => {
				frappe.call({
					method: "pinnacleprod.pinnacle_production.doctype.production_plan.production_plan.check_feasibility",
					args: {
						production_plan: frm.doc.name,
					},
					callback: function (r) {
						if (r.message) {
							frappe.msgprint(r.message);
						}
					},
				});
			});
		}
	},
});
