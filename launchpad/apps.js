/* 런치패드에 올릴 앱 목록 (타일 순서대로) */
sap.ui.define([], () => {
    "use strict";
    return [
        {
            group: "판매 (SD)", items: [
                { id: "so-json", component: "gaon.sojson", title: "판매오더 관리", subtitle: "(a) JSONModel", footer: "JSON 파일", icon: "sap-icon://sales-order", count: "salesOrders", unit: "건" },
                { id: "so-odata", component: "gaon.soodata", title: "판매오더 관리", subtitle: "(b) OData", footer: "MockServer", icon: "sap-icon://sales-order-item", count: "salesOrders", unit: "건" }
            ]
        },
        {
            group: "마스터 데이터", items: [
                { id: "bp", component: "gaon.bp", title: "비즈니스 파트너 조회", subtitle: "고객 · 공급업체", icon: "sap-icon://customer-and-supplier", count: "businessPartners", unit: "명" }
            ]
        },
        {
            group: "재무 (FI · CO)", items: [
                { id: "je", component: "gaon.je", title: "분개 조회", subtitle: "ACDOCA", footer: "Universal Journal", icon: "sap-icon://accounting-document-verification", count: "journalLines", unit: "줄" }
            ]
        },
        {
            group: "SAP GUI 화면 (코스 페이지로 이동)", items: [
                { href: "../course/index.html#s/scr-va01", title: "VA01", subtitle: "판매오더 생성", icon: "sap-icon://sap-box" },
                { href: "../course/index.html#s/data-bp", title: "BP", subtitle: "비즈니스 파트너", icon: "sap-icon://sap-box" },
                { href: "../course/index.html#s/scr-me21n", title: "ME21N", subtitle: "구매오더 생성", icon: "sap-icon://sap-box" },
                { href: "../course/index.html#s/scr-migo", title: "MIGO", subtitle: "입고", icon: "sap-icon://sap-box" },
                { href: "../course/index.html#s/scr-co01", title: "CO01", subtitle: "생산오더 생성", icon: "sap-icon://sap-box" },
                { href: "../course/index.html#s/scr-je", title: "F0717", subtitle: "분개 입력 (Fiori)", icon: "sap-icon://sap-box" },
                { href: "../course/index.html#s/scr-ksb1", title: "KSB1", subtitle: "원가센터 실적 라인", icon: "sap-icon://sap-box" }
            ]
        },
        {
            group: "코스", items: [
                { href: "../course/index.html", title: "S/4HANA 모듈 코스", subtitle: "12장 60단계 · 순서대로", icon: "sap-icon://learning-assistant" }
            ]
        }
    ];
});
