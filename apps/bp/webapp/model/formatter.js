sap.ui.define([
    "sap/ui/core/format/NumberFormat"
], (NumberFormat) => {
    "use strict";

    const oAmount = NumberFormat.getFloatInstance({ groupingEnabled: true, maxFractionDigits: 0 });
    // BP 역할: SAP Learning(FLVN00/01) · SAP Community(FLCU00/01) 자료로 확인
    const ROLE = {
        FLCU00: "FI 고객 · 회사코드 데이터 (조정계정, 지급조건)",
        FLCU01: "고객 · 판매 영역 데이터 (통화, 지급조건, 인코텀즈)",
        FLVN00: "FI 공급업체 · 회사코드 데이터 (조정계정, 지급조건)",
        FLVN01: "공급업체 · 구매조직 데이터 (구매 통화, 지급조건)"
    };

    return {
        roleText(sRole) {
            return ROLE[sRole] || sRole;
        },
        /** 역할 배열 → "FLCU00, FLCU01" */
        roles(aRoles) {
            return (aRoles || []).map((r) => r.BusinessPartnerRole).join(", ");
        },
        categoryText(s) {
            return { 1: "1 개인", 2: "2 조직", 3: "3 그룹" }[s] || s;
        },
        groupingText(s) {
            return { CUST: "CUST 고객", SUPL: "SUPL 공급업체" }[s] || s;
        },
        /** 첫 번째 주소의 도시 */
        city(aAddr) {
            return aAddr && aAddr[0] ? `${aAddr[0].CityName} (${aAddr[0].Country})` : "";
        },
        codeText(sCode, oMap) {
            if (!sCode) {
                return "";
            }
            return oMap && oMap[sCode] ? `${sCode} ${oMap[sCode]}` : sCode;
        },
        amount(v) {
            return oAmount.format(Number(v) || 0);
        }
    };
});
