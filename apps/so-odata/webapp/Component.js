sap.ui.define([
    "sap/ui/core/UIComponent",
    "gaon/soodata/model/models",
    "gaon/soodata/localService/mockserver",
    "gaon/soodata/ext/Inspector"
], (UIComponent, models, mockserver, Inspector) => {
    "use strict";

    // [OData] 진짜 S/4HANA 서버가 없으므로, 앱이 데이터를 요청하기 전에 브라우저 안에 가짜 OData 서버를 켭니다.
    //         실무 앱에는 이 줄이 없고, manifest.json의 /sap/opu/odata/sap/API_SALES_ORDER_SRV/ 로 진짜 서버가 응답합니다.
    mockserver.init();

    return UIComponent.extend("gaon.soodata.Component", {
        metadata: {
            manifest: "json",
            interfaces: ["sap.ui.core.IAsyncContentCreation"]
        },

        init() {
            UIComponent.prototype.init.apply(this, arguments);
            this.setModel(models.createDeviceModel(), "device");

            // [OData] 목록은 서버가 $top/$skip으로 잘라 보내므로 sizeLimit을 늘릴 필요가 없습니다 ((a)와 비교).

            this.getRouter().initialize();
            Inspector.attach(this);
        }
    });
});
