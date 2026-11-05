sap.ui.define([
    "sap/ui/core/mvc/Controller",
    "sap/ui/model/json/JSONModel",
    "sap/ui/model/Filter",
    "sap/ui/model/FilterOperator"
], (Controller, JSONModel, Filter, FilterOperator) => {
    "use strict";

    return Controller.extend("gaon.sojson.controller.List", {
        onInit() {
            // 화면 상태용 모델 (SAP 데이터가 아님)
            this.getView().setModel(new JSONModel({ tableTitle: "판매오더" }), "view");
        },

        onUpdateFinished(oEvent) {
            const iTotal = oEvent.getParameter("total");
            this.getView().getModel("view").setProperty("/tableTitle", `판매오더 (${iTotal}건)`);
        },

        onLiveSearch() {
            clearTimeout(this._iTimer);
            this._iTimer = setTimeout(() => this.onFilter(), 300);
        },

        /** 검색칸·판매조직·처리 상태로 Filter를 만들어 목록 바인딩에 겁니다.
         *  [JSON] 데이터가 이미 브라우저에 있으므로 브라우저 안에서 걸러집니다. */
        onFilter() {
            const aFilters = [];
            const sQuery = this.byId("search").getValue().trim();
            if (sQuery) {
                aFilters.push(new Filter({
                    filters: [
                        new Filter("SalesOrder", FilterOperator.Contains, sQuery),
                        new Filter("PurchaseOrderByCustomer", FilterOperator.Contains, sQuery)
                    ],
                    and: false
                }));
            }
            const sOrg = this.byId("selOrg").getSelectedKey();
            if (sOrg) {
                aFilters.push(new Filter("SalesOrganization", FilterOperator.EQ, sOrg));
            }
            const sStatus = this.byId("selStatus").getSelectedKey();
            if (sStatus) {
                aFilters.push(new Filter("OverallSDProcessStatus", FilterOperator.EQ, sStatus));
            }
            this.byId("soTable").getBinding("items").filter(
                aFilters.length ? new Filter({ filters: aFilters, and: true }) : [], "Application");
        },

        onPress(oEvent) {
            const sSalesOrder = oEvent.getSource().getBindingContext().getProperty("SalesOrder");
            this.getOwnerComponent().getRouter().navTo("detail", { salesOrder: sSalesOrder });
        }
    });
});
