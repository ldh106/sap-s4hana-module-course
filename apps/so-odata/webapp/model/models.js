sap.ui.define([
    "sap/ui/model/json/JSONModel",
    "sap/ui/Device"
], (JSONModel, Device) => {
    "use strict";

    return {
        /** 화면 크기 등 기기 정보를 담은 device 모델 (Fiori 템플릿 기본) */
        createDeviceModel() {
            const oModel = new JSONModel(Device);
            oModel.setDefaultBindingMode("OneWay");
            return oModel;
        }
    };
});
