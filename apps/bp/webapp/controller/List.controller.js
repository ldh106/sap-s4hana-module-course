sap.ui.define([
    "sap/ui/core/mvc/Controller",
    "sap/ui/model/json/JSONModel",
    "sap/ui/model/Filter",
    "sap/ui/model/FilterOperator"
], (Controller, JSONModel, Filter, FilterOperator) => {
    "use strict";

    return Controller.extend("gaon.bp.controller.List", {
        onInit() {
            this.getView().setModel(new JSONModel({ tableTitle: "BP" }), "view");
        },

        onUpdateFinished(oEvent) {
            this.getView().getModel("view").setProperty("/tableTitle", `BP (${oEvent.getParameter("total")}명)`);
        },

        onFilter() {
            const aFilters = [];
            const sQuery = this.byId("search").getValue().trim();
            if (sQuery) {
                aFilters.push(new Filter({
                    filters: [
                        new Filter("BusinessPartner", FilterOperator.Contains, sQuery),
                        new Filter("OrganizationBPName1", FilterOperator.Contains, sQuery)
                    ],
                    and: false
                }));
            }
            // 고객 = Customer 번호가 있는 BP (CVI로 고객 레코드가 연결됨), 공급업체도 같은 방식
            const sKind = this.byId("selKind").getSelectedKey();
            if (sKind === "C") {
                aFilters.push(new Filter("Customer", FilterOperator.NE, ""));
            } else if (sKind === "S") {
                aFilters.push(new Filter("Supplier", FilterOperator.NE, ""));
            }
            this.byId("bpTable").getBinding("items").filter(aFilters.length ? new Filter({ filters: aFilters, and: true }) : [], "Application");
        },

        onPress(oEvent) {
            const sPartner = oEvent.getSource().getBindingContext().getProperty("BusinessPartner");
            this.getOwnerComponent().getRouter().navTo("detail", { partner: sPartner });
        }
    });
});
