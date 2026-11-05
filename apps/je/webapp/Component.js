sap.ui.define([
    "sap/ui/core/UIComponent",
    "gaon/je/model/models",
    "gaon/je/ext/Inspector"
], (UIComponent, models, Inspector) => {
    "use strict";

    return UIComponent.extend("gaon.je.Component", {
        metadata: {
            manifest: "json",
            interfaces: ["sap.ui.core.IAsyncContentCreation"]
        },

        init() {
            UIComponent.prototype.init.apply(this, arguments);
            this.setModel(models.createDeviceModel(), "device");
            // JSONModel 목록 한도(기본 100)를 ACDOCA 라인 수보다 크게
            this.getModel().setSizeLimit(20000);
            this.getRouter().initialize();
            Inspector.attach(this);
        }
    });
});
