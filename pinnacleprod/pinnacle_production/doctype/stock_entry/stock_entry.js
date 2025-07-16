frappe.ui.form.on("Stock Entry", {
	onload: function (frm) {
		if (frm.doc.work_order) {
			frappe.db.get_doc("Work Order", frm.doc.work_order).then((work_order) => {
				if (work_order.sales_order) {
					frappe.db
						.get_doc("Sales Order", work_order.sales_order)
						.then((sales_order) => {
							frm.doc.items.forEach((item_row) => {
								const so_item = sales_order.items.find(
									(so_itm) => so_itm.item_code === item_row.item_code
								);
								if (so_item) {
									// Calculate total amount before updating qty
									const total_amount = item_row.qty * item_row.basic_rate;

									// Update fields from sales order
									item_row.qty = so_item.qty;
									item_row.basic_rate = total_amount / so_item.qty;
								}
							});
							frm.refresh_field("items");
						});
				}
			});
		}
	},
});
