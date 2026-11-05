sap.ui.define([
    "sap/ui/core/mvc/Controller"
], (Controller) => {
    "use strict";

    return Controller.extend("gaon.bp.controller.Detail", {
        onInit() {
            this.getOwnerComponent().getRouter().getRoute("detail").attachPatternMatched(this._onMatched, this);
        },

        _onMatched(oEvent) {
            const sPartner = oEvent.getParameter("arguments").partner;
            const oModel = this.getView().getModel();
            // JSON 배열에서 위치를 찾아 경로를 만듭니다: /A_BusinessPartner/3
            oModel.dataLoaded().then(() => {
                const iIndex = (oModel.getProperty("/A_BusinessPartner") || []).findIndex((b) => b.BusinessPartner === sPartner);
                this.getView().bindElement({ path: "/A_BusinessPartner/" + iIndex });
                this.byId("objectPage").setSelectedSection(this.byId("secGeneral"));
            });
        },

        onClose() {
            this.getOwnerComponent().getRouter().navTo("list");
        }
    });
});
