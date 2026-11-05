sap.ui.define([
    "sap/ui/core/UIComponent",
    "gaon/bp/model/models",
    "gaon/bp/ext/Inspector"
], (UIComponent, models, Inspector) => {
    "use strict";

    return UIComponent.extend("gaon.bp.Component", {
        metadata: {
            manifest: "json",
            interfaces: ["sap.ui.core.IAsyncContentCreation"]
        },

        init() {
            UIComponent.prototype.init.apply(this, arguments);
            this.setModel(models.createDeviceModel(), "device");
            this.getRouter().initialize();
            Inspector.attach(this);
        }
    });
});
