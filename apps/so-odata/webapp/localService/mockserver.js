sap.ui.define([
    "sap/ui/core/util/MockServer"
], (MockServer) => {
    "use strict";

    // 실제 서비스 주소와 똑같이 둡니다. 앱 코드(manifest, 컨트롤러)는 이 파일이 있는지 모릅니다.
    const SERVICE_URL = "/sap/opu/odata/sap/API_SALES_ORDER_SRV/";

    return {
        /**
         * 브라우저 안에 가짜 OData V2 서버를 켭니다.
         * metadata.xml(서비스 구조)과 mockdata/*.json(데이터)을 읽고,
         * $filter · $orderby · $top · $skip · $count · 내비게이션(to_Item) 요청에 답합니다.
         */
        init() {
            const sLocal = sap.ui.require.toUrl("gaon/soodata/localService");
            const oMockServer = new MockServer({ rootUri: SERVICE_URL });
            // 실제 네트워크처럼 조금 늦게 답하게 해서, 화면이 "기다리는" 모습도 보이게 합니다
            MockServer.config({ autoRespond: true, autoRespondAfter: 250 });
            oMockServer.simulate(sLocal + "/metadata.xml", {
                sMockdataBaseUrl: sLocal + "/mockdata",
                bGenerateMissingMockData: false
            });
            oMockServer.start();
            return oMockServer;
        }
    };
});
