sap.ui.define([
    "sap/ui/core/format/NumberFormat"
], (NumberFormat) => {
    "use strict";

    const oAmount = NumberFormat.getFloatInstance({ groupingEnabled: true, maxFractionDigits: 2 });

    const STATUS = { A: "미처리", B: "처리 중", C: "완료" };

    return {
        /** 처리 상태 코드(A/B/C) → 글자 */
        statusText(s) {
            return STATUS[s] || s || "";
        },
        /** 처리 상태 코드 → ObjectStatus 색 */
        statusState(s) {
            return { A: "Warning", B: "Information", C: "Success" }[s] || "None";
        },
        /** 고객 번호 → 이름. 이름은 판매오더 API에 없어서 보조 모델(cust)에서 찾습니다 */
        customerName(sId, oMap) {
            return (oMap && oMap[sId] && oMap[sId].name) || "";
        },
        /** 코드 + 이름 (예: 1100 국내영업) */
        codeText(sCode, oMap) {
            if (!sCode) {
                return "";
            }
            return oMap && oMap[sCode] ? `${sCode} ${oMap[sCode]}` : sCode;
        },
        /** 후속 문서 범주 → 아이콘 */
        docCategoryIcon(c) {
            return { J: "sap-icon://shipping-status", R: "sap-icon://product", M: "sap-icon://loan" }[c] || "sap-icon://document";
        },
        /** 차변(S) / 대변(H) */
        drcr(d) {
            return d === "S" ? "차변" : d === "H" ? "대변" : d;
        },
        /** ACDOCA는 대변 금액을 음수로 저장합니다. 화면에는 절댓값으로 */
        absAmount(v) {
            return Math.abs(Number(v) || 0);
        },
        /** 금액을 절댓값 + 천 단위 쉼표로 (예: -3278400 → 3,278,400) */
        amount(v) {
            return oAmount.format(Math.abs(Number(v) || 0));
        }
    };
});
