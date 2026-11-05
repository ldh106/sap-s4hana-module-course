sap.ui.define([
    "sap/ui/core/mvc/Controller",
    "sap/ui/model/json/JSONModel",
    "sap/ui/core/routing/History"
], (Controller, JSONModel, History) => {
    "use strict";

    return Controller.extend("gaon.sojson.controller.Detail", {
        onInit() {
            this.getView().setModel(new JSONModel({ acc: [] }), "view");
            this.getOwnerComponent().getRouter().getRoute("detail").attachPatternMatched(this._onMatched, this);
        },

        _onMatched(oEvent) {
            const sSalesOrder = oEvent.getParameter("arguments").salesOrder;
            const oModel = this.getView().getModel();

            // [JSON] 파일을 다 읽은 뒤(dataLoaded) 배열에서 위치를 찾아 경로를 만듭니다: /A_SalesOrder/39
            oModel.dataLoaded().then(() => {
                const aOrders = oModel.getProperty("/A_SalesOrder") || [];
                const iIndex = aOrders.findIndex((o) => o.SalesOrder === sSalesOrder);
                this.getView().bindElement({ path: "/A_SalesOrder/" + iIndex });
            });

            const oAcc = this.getView().getModel("acc");
            oAcc.dataLoaded().then(() => {
                this.getView().getModel("view").setProperty("/acc", oAcc.getProperty("/" + sSalesOrder) || []);
            });
            this.byId("objectPage").setSelectedSection(this.byId("secSalesArea"));
        },

        onShowLines(oEvent) {
            const oContext = oEvent.getSource().getBindingContext("view");
            // Fragment는 처음 한 번만 만들고 다시 씁니다
            this._pLines ??= this.loadFragment({ name: "gaon.sojson.view.Lines" });
            this._pLines.then((oDialog) => {
                oDialog.bindElement({ path: oContext.getPath(), model: "view" });
                oDialog.open();
            });
        },

        onCloseLines() {
            this.byId("linesDialog").close();
        },

        onNavBack() {
            if (History.getInstance().getPreviousHash() !== undefined) {
                window.history.go(-1);
            } else {
                this.getOwnerComponent().getRouter().navTo("list", {}, true);
            }
        }
    });
});
