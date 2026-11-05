sap.ui.define([
    "sap/ui/core/UIComponent",
    "gaon/sojson/model/models",
    "gaon/sojson/ext/Inspector"
], (UIComponent, models, Inspector) => {
    "use strict";

    return UIComponent.extend("gaon.sojson.Component", {
        metadata: {
            manifest: "json",
            interfaces: ["sap.ui.core.IAsyncContentCreation"]
        },

        init() {
            UIComponent.prototype.init.apply(this, arguments);
            this.setModel(models.createDeviceModel(), "device");

            // [JSON] JSONModel은 목록 바인딩을 기본 100건까지만 보여줍니다(sizeLimit).
            //        판매오더가 237건이라 한도를 늘립니다. OData 모델에는 이 줄이 필요 없습니다.
            this.getModel().setSizeLimit(1000);

            this.getRouter().initialize();
            Inspector.attach(this);
        }
    });
});
