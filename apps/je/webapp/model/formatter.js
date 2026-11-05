sap.ui.define([
    "sap/ui/core/format/NumberFormat"
], (NumberFormat) => {
    "use strict";

    const oAmount = NumberFormat.getFloatInstance({ groupingEnabled: true, maxFractionDigits: 2 });

    return {
        codeText(sCode, oMap) {
            if (!sCode) {
                return "";
            }
            return oMap && oMap[sCode] ? `${sCode} ${oMap[sCode]}` : sCode;
        },
        drcr(d) {
            return d === "S" ? "S 차변" : d === "H" ? "H 대변" : d;
        },
        /** ACDOCA 그대로: 대변은 음수 */
        signedAmount(v) {
            return v === undefined ? "" : oAmount.format(Number(v));
        },
        /** 절댓값 */
        amount(v) {
            return oAmount.format(Math.abs(Number(v) || 0));
        },
        /** 차변 칸: 차변일 때만 */
        debit(v, d) {
            return d === "S" ? oAmount.format(Math.abs(Number(v))) : "";
        },
        /** 대변 칸: 대변일 때만 */
        credit(v, d) {
            return d === "H" ? oAmount.format(Math.abs(Number(v))) : "";
        }
    };
});
