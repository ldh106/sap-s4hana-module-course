sap.ui.define([
    "sap/ui/core/mvc/Controller",
    "sap/ui/model/json/JSONModel",
    "sap/ui/model/Filter",
    "sap/ui/model/FilterOperator",
    "sap/ui/core/format/NumberFormat"
], (Controller, JSONModel, Filter, FilterOperator, NumberFormat) => {
    "use strict";

    const oAmount = NumberFormat.getFloatInstance({ groupingEnabled: true, maxFractionDigits: 2 });

    return Controller.extend("gaon.je.controller.Main", {
        onInit() {
            // 화면 상태 모델 (필터 목록, 합계)
            this.getView().setModel(new JSONModel({ types: [], accounts: [], costCenters: [], title: "", debit: "", credit: "" }), "view");
            // 전표 팝업 모델
            this.getView().setModel(new JSONModel({}), "doc");

            const oModel = this.getOwnerComponent().getModel();
            oModel.dataLoaded().then(() => {
                const oView = this.getView().getModel("view");
                const mType = oModel.getProperty("/BLART"), mGl = oModel.getProperty("/GL"), mCc = oModel.getProperty("/CC");
                oView.setProperty("/types", [{ key: "", text: "전체" }].concat(Object.keys(mType).sort().map((k) => ({ key: k, text: `${k} ${mType[k]}` }))));
                oView.setProperty("/accounts", Object.keys(mGl).sort().map((k) => ({ key: k, text: `${k} ${mGl[k]}` })));
                oView.setProperty("/costCenters", [{ key: "", text: "전체" }].concat(Object.keys(mCc).sort().map((k) => ({ key: k, text: `${k} ${mCc[k]}` }))));
            });
            // 표가 처음 행을 그린 뒤 한 번 합계를 계산합니다 (그 전에는 rows 바인딩이 아직 없음)
            this.byId("jeTable").attachEventOnce("rowsUpdated", () => this._updateSums());
        },

        /** 필터를 모아 rows 바인딩에 겁니다 (JSONModel이라 브라우저 안에서 걸러짐) */
        onFilter() {
            const aFilters = [];
            const add = (sPath, sValue) => { if (sValue) { aFilters.push(new Filter(sPath, FilterOperator.EQ, sValue)); } };
            add("POPER", this.byId("selPeriod").getSelectedKey());
            add("BLART", this.byId("selType").getSelectedKey());
            add("RACCT", this.byId("cbAcct").getSelectedKey());
            add("RCNTR", this.byId("selCc").getSelectedKey());
            const sQuery = this.byId("search").getValue().trim();
            if (sQuery) {
                aFilters.push(new Filter({
                    filters: ["BELNR", "AWREF", "SGTXT"].map((p) => new Filter(p, FilterOperator.Contains, sQuery)),
                    and: false
                }));
            }
            this.byId("jeTable").getBinding("rows").filter(aFilters.length ? new Filter({ filters: aFilters, and: true }) : [], "Application");
            this._updateSums();
        },

        /** 걸러진 라인의 차변·대변 합계. 전표 단위로 거르면 둘이 항상 같습니다 */
        _updateSums() {
            const oBinding = this.byId("jeTable").getBinding("rows");
            if (!oBinding) {
                return;
            }
            const aCtx = oBinding.getContexts(0, oBinding.getLength());
            let fDebit = 0, fCredit = 0;
            aCtx.forEach((c) => {
                const v = c.getProperty("HSL");
                if (c.getProperty("DRCRK") === "S") { fDebit += v; } else { fCredit -= v; }
            });
            const oView = this.getView().getModel("view");
            const bBal = Math.abs(fDebit - fCredit) < 0.5;
            oView.setData(Object.assign(oView.getData(), {
                title: `회계 라인 ${oAmount.format(oBinding.getLength())}줄`,
                debit: oAmount.format(fDebit),
                credit: oAmount.format(fCredit),
                balanceText: bBal ? "차변 = 대변" : `차이 ${oAmount.format(fDebit - fCredit)} (계정·원가센터로 거르면 한쪽만 보입니다)`,
                balanceState: bBal ? "Success" : "Information",
                balanceIcon: bBal ? "sap-icon://accept" : "sap-icon://hint"
            }));
        },

        /** 전표 번호를 누르면 같은 BELNR의 라인을 모두 모아 팝업(Fragment)으로 보여줍니다 */
        onOpenDoc(oEvent) {
            const oModel = this.getView().getModel();
            const sBelnr = oEvent.getSource().getBindingContext().getProperty("BELNR");
            const aLines = oModel.getProperty("/ACDOCA").filter((r) => r.BELNR === sBelnr);
            const mGl = oModel.getProperty("/GL");
            const oHead = oModel.getProperty("/BKPF/" + sBelnr) || {};
            const fDebit = aLines.filter((l) => l.DRCRK === "S").reduce((s, l) => s + l.HSL, 0);
            const fCredit = -aLines.filter((l) => l.DRCRK === "H").reduce((s, l) => s + l.HSL, 0);
            const first = aLines[0] || {};
            this.getView().getModel("doc").setData({
                BELNR: sBelnr, RBUKRS: first.RBUKRS, GJAHR: first.GJAHR, BLART: first.BLART, blartName: (oModel.getProperty("/BLART") || {})[first.BLART] || "",
                BUDAT: first.BUDAT, AWTYP: first.AWTYP, AWREF: first.AWREF, BKTXT: oHead.BKTXT,
                lines: aLines.map((l) => Object.assign({ name: mGl[l.RACCT] || "" }, l)),
                debit: oAmount.format(fDebit), credit: oAmount.format(fCredit), balanced: Math.abs(fDebit - fCredit) < 0.5
            });
            this._pDoc ??= this.loadFragment({ name: "gaon.je.view.JournalEntry" });
            this._pDoc.then((oDialog) => oDialog.open());
        },

        onCloseDoc() {
            this.byId("docDialog").close();
        }
    });
});
