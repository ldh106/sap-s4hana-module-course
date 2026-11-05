sap.ui.define([
    "sap/ui/core/mvc/Controller",
    "sap/ui/model/json/JSONModel",
    "sap/ui/Device"
], (Controller, JSONModel, Device) => {
    "use strict";

    return Controller.extend("gaon.bp.controller.App", {
        onInit() {
            const oApp = new JSONModel({ layout: "OneColumn" });
            this.getView().setModel(oApp, "app");
            // 어느 화면(route)이냐에 따라 열 배치를 바꿉니다
            this.getOwnerComponent().getRouter().attachRouteMatched((oEvent) => {
                const bDetail = oEvent.getParameter("name") === "detail";
                oApp.setProperty("/layout", !bDetail ? "OneColumn" : (Device.system.phone ? "MidColumnFullScreen" : "TwoColumnsMidExpanded"));
            });
        }
    });
});
