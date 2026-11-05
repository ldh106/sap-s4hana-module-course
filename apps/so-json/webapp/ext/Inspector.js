/*
 * 구성 보기 (Inspector) — 모든 앱이 같이 쓰는 파일입니다.
 * 원본: shared/ext/Inspector.js → tools/sync_shared.py 가 각 앱 webapp/ext/ 로 복사합니다.
 *
 * 화면 오른쪽 아래 "구성 보기"를 켜면:
 *   - 마우스를 올린 컨트롤에 테두리가 생기고
 *   - 누르면 (앱 동작 대신) 그 컨트롤의 정체를 오른쪽 패널에 보여줍니다:
 *     컨트롤 클래스와 역할, 화면 안의 위치(부모 컨트롤), 바인딩 경로와 현재 값,
 *     그 값이 SAP의 어느 테이블-필드에 저장되는지, 이 앱의 모델과 OData 요청 기록.
 */
sap.ui.define([
	"sap/ui/core/Element"
], (Element) => {
	"use strict";

	// ───────── 컨트롤 설명 ─────────
	const CONTROL_DOC = {
		"sap.m.App": "화면(Page)을 바꿔 끼우는 최상위 컨테이너입니다. 라우터가 여기 pages에 뷰를 넣습니다.",
		"sap.f.FlexibleColumnLayout": "목록-상세를 2~3열로 나란히 보여주는 Fiori 레이아웃입니다. 라우터가 beginColumnPages / midColumnPages에 뷰를 넣습니다.",
		"sap.ui.core.mvc.XMLView": "XML로 정의한 뷰입니다. 같은 이름의 컨트롤러와 짝을 이룹니다.",
		"sap.f.DynamicPage": "Fiori 목록 화면의 기본 틀입니다. 제목(title) · 필터 영역(header) · 본문(content)으로 나뉘고, 스크롤하면 헤더가 접힙니다.",
		"sap.f.DynamicPageTitle": "DynamicPage 맨 위 제목 줄입니다. 제목(heading)과 오른쪽 버튼(actions)을 둡니다.",
		"sap.f.DynamicPageHeader": "DynamicPage의 접히는 헤더입니다. 보통 검색·필터를 둡니다.",
		"sap.uxap.ObjectPageLayout": "문서 하나를 자세히 보여주는 Fiori 상세 화면(Object Page)입니다. 헤더 + 섹션으로 되어 있고, 섹션 제목이 위쪽 앵커 바에 탭처럼 나옵니다.",
		"sap.uxap.ObjectPageDynamicHeaderTitle": "Object Page의 제목 영역입니다. 펼친 상태(expandedContent)와 접힌 상태(snappedContent)에 다른 내용을 둘 수 있습니다.",
		"sap.uxap.ObjectPageSection": "Object Page의 섹션입니다. 위쪽 앵커 바에 탭처럼 나타납니다.",
		"sap.uxap.ObjectPageSubSection": "섹션 안의 묶음입니다. 실제 내용은 blocks에 들어갑니다.",
		"sap.m.Page": "가장 기본적인 화면 틀(제목 + 내용)입니다.",
		"sap.m.Table": "반응형 표입니다. items 바인딩 하나로 데이터 건수만큼 행(ColumnListItem)을 찍어냅니다. 화면이 좁으면 열을 아래로 접습니다.",
		"sap.m.Column": "sap.m.Table의 열 정의(머리글, 너비, 정렬, 좁은 화면에서 숨길지)입니다.",
		"sap.m.ColumnListItem": "sap.m.Table의 한 행입니다. items 바인딩의 템플릿이라서 데이터 건수만큼 복제됩니다. type=\"Navigation\"이면 누를 수 있습니다.",
		"sap.ui.table.Table": "그리드 표(데스크톱용)입니다. 보이는 행만 그리는 가상 스크롤이라 수천 건도 가볍게 보여줍니다. rows 바인딩을 씁니다.",
		"sap.ui.table.Column": "그리드 표의 열입니다. template 안의 컨트롤이 각 셀이 됩니다.",
		"sap.m.Text": "읽기 전용 글자입니다.",
		"sap.m.Label": "입력칸이나 값 앞에 붙는 이름표입니다.",
		"sap.m.Title": "제목 글자입니다.",
		"sap.m.Link": "누를 수 있는 글자입니다.",
		"sap.m.ObjectIdentifier": "문서 번호처럼 '무엇인지'를 나타내는 굵은 제목(title) + 보조 글자(text)입니다.",
		"sap.m.ObjectNumber": "금액·수량 표시용입니다. 숫자(number)와 단위·통화(unit)를 함께 보여줍니다.",
		"sap.m.ObjectStatus": "상태 표시입니다. state(Success · Warning · Error · Information)에 따라 색이 바뀝니다.",
		"sap.m.ObjectAttribute": "'이름: 값' 한 줄입니다.",
		"sap.m.SearchField": "검색 입력칸입니다. 컨트롤러에서 Filter를 만들어 목록 바인딩에 겁니다.",
		"sap.m.Select": "드롭다운 선택입니다. selectedKey로 고른 값을 읽습니다.",
		"sap.m.ComboBox": "입력하면서 고르는 드롭다운입니다.",
		"sap.m.SegmentedButton": "여러 개 중 하나를 고르는 버튼 묶음입니다.",
		"sap.m.Button": "버튼입니다. press 이벤트가 컨트롤러 함수를 부릅니다.",
		"sap.m.OverflowToolbar": "버튼·제목을 가로로 늘어놓는 줄입니다. 공간이 모자라면 버튼을 ⋯ 메뉴로 넘깁니다.",
		"sap.m.Toolbar": "버튼·제목을 가로로 늘어놓는 줄입니다.",
		"sap.m.MessageStrip": "안내 메시지 띠입니다.",
		"sap.m.Dialog": "팝업 창입니다. 이 앱들은 Fragment(XML 조각)로 정의하고 loadFragment로 엽니다.",
		"sap.ui.layout.form.SimpleForm": "라벨-값 쌍을 격자로 배치하는 폼입니다. Label 바로 다음 컨트롤이 그 라벨의 값이 됩니다.",
		"sap.m.VBox": "안의 컨트롤을 세로로 쌓는 상자입니다.",
		"sap.m.HBox": "안의 컨트롤을 가로로 늘어놓는 상자입니다.",
		"sap.m.GenericTile": "런치패드 타일입니다.",
		"sap.f.ShellBar": "Fiori 런치패드 맨 위 막대입니다.",
		"sap.m.IconTabBar": "탭 화면입니다."
	};

	// ───────── 바인딩 속성 → SAP 테이블-필드 ─────────
	const F = (t, ko) => ({ t, ko });
	const ACD = {
		RLDNR: F("ACDOCA-RLDNR", "원장 (0L = 기본 원장)"), RBUKRS: F("ACDOCA-RBUKRS", "회사코드"), GJAHR: F("ACDOCA-GJAHR", "회계연도"),
		BELNR: F("ACDOCA-BELNR", "회계 전표 번호"), DOCLN: F("ACDOCA-DOCLN", "전표 안의 라인 번호"), BLART: F("ACDOCA-BLART", "전표 유형"),
		BUDAT: F("ACDOCA-BUDAT", "전기일"), POPER: F("ACDOCA-POPER", "회계 기간 (월)"), RACCT: F("ACDOCA-RACCT", "G/L 계정"),
		DRCRK: F("ACDOCA-DRCRK", "차변(S) / 대변(H)"), HSL: F("ACDOCA-HSL", "회사코드 통화 금액"), RHCUR: F("ACDOCA-RHCUR", "회사코드 통화"),
		WSL: F("ACDOCA-WSL", "거래 통화 금액"), RWCUR: F("ACDOCA-RWCUR", "거래 통화"), RCNTR: F("ACDOCA-RCNTR", "원가센터"),
		AUFNR: F("ACDOCA-AUFNR", "오더 번호 (생산오더 등)"), PRCTR: F("ACDOCA-PRCTR", "손익센터"), KUNNR: F("ACDOCA-KUNNR", "고객"),
		LIFNR: F("ACDOCA-LIFNR", "공급업체"), MATNR: F("ACDOCA-MATNR", "자재"), WERKS: F("ACDOCA-WERKS", "플랜트"),
		AWTYP: F("ACDOCA-AWTYP", "참조 문서 종류 (VBRK 청구, MKPF 자재문서 등)"), AWREF: F("ACDOCA-AWREF", "참조 문서 번호"), SGTXT: F("ACDOCA-SGTXT", "라인 텍스트")
	};
	const FIELDMAP = {
		A_SalesOrder: {
			SalesOrder: F("VBAK-VBELN", "판매오더 번호"), SalesOrderType: F("VBAK-AUART", "판매문서 유형"), SalesOrganization: F("VBAK-VKORG", "판매조직"),
			DistributionChannel: F("VBAK-VTWEG", "유통경로"), OrganizationDivision: F("VBAK-SPART", "제품군"), SoldToParty: F("VBAK-KUNNR", "판매처 (주문 고객)"),
			CreationDate: F("VBAK-ERDAT", "생성일"), SalesOrderDate: F("VBAK-AUDAT", "문서 일자"), PurchaseOrderByCustomer: F("VBAK-BSTNK", "고객 참조 (고객 PO 번호)"),
			RequestedDeliveryDate: F("VBAK-VDATU", "희망 납기"), TotalNetAmount: F("VBAK-NETWR", "순금액"), TransactionCurrency: F("VBAK-WAERK", "문서 통화"),
			CustomerPaymentTerms: F("VBKD-ZTERM", "지급조건 (비즈니스 데이터 테이블)"), IncotermsClassification: F("VBKD-INCO1", "인코텀즈 (비즈니스 데이터 테이블)"),
			OverallSDProcessStatus: F("VBAK-GBSTK", "전체 처리 상태 (A 미처리 · B 처리 중 · C 완료)"), OverallDeliveryStatus: F("VBAK-LFSTK", "납품 상태 (A · B · C)")
		},
		A_SalesOrderItem: {
			SalesOrder: F("VBAP-VBELN", "판매오더 번호"), SalesOrderItem: F("VBAP-POSNR", "아이템 번호"), SalesOrderItemCategory: F("VBAP-PSTYV", "품목 범주"),
			SalesOrderItemText: F("VBAP-ARKTX", "아이템 내역"), Material: F("VBAP-MATNR", "자재"), RequestedQuantity: F("VBAP-KWMENG", "주문 수량"),
			RequestedQuantityUnit: F("VBAP-VRKME", "판매 단위"), NetAmount: F("VBAP-NETWR", "아이템 순금액"), TransactionCurrency: F("VBAP-WAERK", "통화"),
			ProductionPlant: F("VBAP-WERKS", "플랜트"), SDProcessStatus: F("VBAP-GBSTA", "아이템 처리 상태")
		},
		A_SalesOrderSubsqntProcFlow: {
			SalesOrder: F("VBFA-VBELV", "앞 문서 (판매오더)"), SubsequentDocument: F("VBFA-VBELN", "후속 문서 번호"),
			SubsequentDocumentCategory: F("VBFA-VBTYP_N", "후속 문서 범주 (J 출하 · R 재고 이동 · M 청구)"), CreationDate: F("VBFA-ERDAT", "생성일")
		},
		A_BusinessPartner: {
			BusinessPartner: F("BUT000-PARTNER", "BP 번호"), BusinessPartnerCategory: F("BUT000-TYPE", "BP 범주 (1 개인 · 2 조직 · 3 그룹)"),
			BusinessPartnerGrouping: F("BUT000-BU_GROUP", "그룹핑 (번호 범위와 화면 구성을 정함)"), OrganizationBPName1: F("BUT000-NAME_ORG1", "조직 이름 1"),
			BusinessPartnerFullName: F("BUT000 이름 필드", "전체 이름 (이름 필드를 합친 값)"), SearchTerm1: F("BUT000-BU_SORT1", "검색어 1"),
			Customer: F("KNA1-KUNNR", "연결된 고객 번호 (CVI)"), Supplier: F("LFA1-LIFNR", "연결된 공급업체 번호 (CVI)")
		},
		A_BusinessPartnerRole: { BusinessPartnerRole: F("BUT100-RLTYP", "BP 역할"), BusinessPartner: F("BUT100-PARTNER", "BP 번호") },
		A_BusinessPartnerAddress: { CityName: F("ADRC-CITY1", "도시 (주소 테이블)"), Country: F("ADRC-COUNTRY", "국가 (주소 테이블)") },
		A_Customer: { Customer: F("KNA1-KUNNR", "고객 번호"), CustomerName: F("KNA1-NAME1", "고객 이름") },
		A_CustomerCompany: { CompanyCode: F("KNB1-BUKRS", "회사코드"), ReconciliationAccount: F("KNB1-AKONT", "조정계정"), PaymentTerms: F("KNB1-ZTERM", "지급조건 (회사코드)") },
		A_CustomerSalesArea: {
			SalesOrganization: F("KNVV-VKORG", "판매조직"), DistributionChannel: F("KNVV-VTWEG", "유통경로"), Division: F("KNVV-SPART", "제품군"),
			Currency: F("KNVV-WAERS", "통화"), CustomerPaymentTerms: F("KNVV-ZTERM", "지급조건 (판매 영역)"), IncotermsClassification: F("KNVV-INCO1", "인코텀즈"),
			CustomerGroup: F("KNVV-KDGRP", "고객 그룹")
		},
		A_Supplier: { Supplier: F("LFA1-LIFNR", "공급업체 번호"), SupplierName: F("LFA1-NAME1", "공급업체 이름") },
		A_SupplierCompany: { CompanyCode: F("LFB1-BUKRS", "회사코드"), ReconciliationAccount: F("LFB1-AKONT", "조정계정"), PaymentTerms: F("LFB1-ZTERM", "지급조건 (회사코드)") },
		A_SupplierPurchasingOrg: { PurchasingOrganization: F("LFM1-EKORG", "구매조직"), PurchaseOrderCurrency: F("LFM1-WAERS", "구매오더 통화"), PaymentTerms: F("LFM1-ZTERM", "지급조건 (구매조직)") },
		ACDOCA: ACD
	};
	// 경로 조각 → 엔터티 이름 (JSON은 내비게이션 이름, OData는 엔터티 세트 이름이 경로에 나옴)
	const ENTITY = {
		A_SalesOrder: "A_SalesOrder", to_SalesOrder: "A_SalesOrder", to_Item: "A_SalesOrderItem", A_SalesOrderItem: "A_SalesOrderItem",
		to_SubsequentProcFlowDoc: "A_SalesOrderSubsqntProcFlow", A_SalesOrderSubsqntProcFlow: "A_SalesOrderSubsqntProcFlow",
		A_BusinessPartner: "A_BusinessPartner", to_BusinessPartnerRole: "A_BusinessPartnerRole", to_BusinessPartnerAddress: "A_BusinessPartnerAddress",
		to_Customer: "A_Customer", to_CustomerCompany: "A_CustomerCompany", to_CustomerSalesArea: "A_CustomerSalesArea",
		to_Supplier: "A_Supplier", to_SupplierCompany: "A_SupplierCompany", to_SupplierPurchasingOrg: "A_SupplierPurchasingOrg",
		ACDOCA: "ACDOCA", lines: "ACDOCA"
	};
	const AUX = {
		cust: "보조 모델 cust (model/customers.json) — 고객 이름은 API_SALES_ORDER_SRV에 없어서 고객 마스터(KNA1-NAME1)를 따로 읽어 붙입니다.",
		acc: "보조 모델 acc (model/accounting.json) — 판매오더 API에는 회계 전표가 없어서 교육용으로 따로 붙였습니다. 원래 자리는 BKPF · ACDOCA입니다.",
		txt: "보조 모델 txt (model/texts.json) — 코드의 이름(판매조직 1100 = 국내영업 등). 실제로는 각 설정 테이블(TVKO 등)의 텍스트입니다.",
		view: "화면 상태용 모델 view — 컨트롤러가 만든 JSONModel입니다. SAP 데이터가 아니라 화면 표시용 값입니다.",
		doc: "팝업용 모델 doc — 컨트롤러가 고른 전표 한 건의 라인을 담은 JSONModel입니다.",
		i18n: "i18n 모델 — 화면 글자를 담은 i18n.properties 파일입니다."
	};

	const BOUND_PROPS = ["text", "title", "number", "unit", "value", "selectedKey", "state", "visible", "header", "subheader", "description", "info", "intro"];
	const css = `
	.insBtn{position:fixed;right:16px;bottom:16px;z-index:2147483000;font:600 13px/1 system-ui,sans-serif;padding:10px 14px;border-radius:20px;border:1px solid #0a6ed1;background:#fff;color:#0a6ed1;cursor:pointer;box-shadow:0 4px 14px rgba(0,0,0,.18)}
	.insBtn.on{background:#0a6ed1;color:#fff}
	.insHl,.insSel{position:fixed;pointer-events:none;z-index:2147482990;border:2px dashed #e76500;border-radius:3px;display:none}
	.insSel{border:2px solid #e76500;background:rgba(231,101,0,.06)}
	.insTag{position:fixed;height:auto;width:auto;bottom:auto;right:auto;white-space:nowrap;pointer-events:none;z-index:2147482995;background:#e76500;color:#fff;font:600 11px/1.5 ui-monospace,monospace;padding:1px 6px;border-radius:3px;display:none}
	.insPanel{position:fixed;top:0;right:0;bottom:0;width:min(400px,92vw);z-index:2147482998;background:#fff;color:#1d2d3e;border-left:1px solid #d9d9d9;box-shadow:-8px 0 24px rgba(0,0,0,.14);font:14px/1.55 system-ui,"Apple SD Gothic Neo","Malgun Gothic",sans-serif;display:none;flex-direction:column}
	.insPanel.open{display:flex}
	.insHead{display:flex;align-items:center;gap:8px;padding:12px 14px;border-bottom:1px solid #eee;font-weight:700}
	.insHead span{flex:1}
	.insHead button,.insTabs button{font:inherit;font-size:12px;border:1px solid #ccc;background:#fff;border-radius:6px;padding:3px 8px;cursor:pointer}
	.insTabs{display:flex;gap:6px;padding:8px 14px;border-bottom:1px solid #eee}
	.insTabs button[aria-pressed=true]{background:#0a6ed1;border-color:#0a6ed1;color:#fff}
	.insBody{overflow:auto;padding:12px 14px 80px;flex:1}
	.insBody h4{margin:14px 0 6px;font-size:12px;color:#6a6d70;text-transform:none;letter-spacing:.02em}
	.insBody code,.insMono{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:12.5px}
	.insCls{font:700 15px/1.3 ui-monospace,monospace;color:#0a6ed1;word-break:break-all}
	.insPath{display:flex;flex-wrap:wrap;gap:4px;font-size:12px}
	.insPath span{background:#f2f4f6;border-radius:4px;padding:1px 6px}
	.insRow{border:1px solid #e5e5e5;border-radius:8px;padding:8px 10px;margin:6px 0;display:grid;gap:3px}
	.insRow b{font-size:12px;color:#6a6d70;font-weight:600}
	.insRow code,.insRow span{overflow-wrap:anywhere}
	.insSap{display:inline-block;background:#fff3e0;color:#a14a00;border-radius:4px;padding:0 6px;font:700 12.5px/1.6 ui-monospace,monospace}
	.insNote{font-size:12.5px;color:#6a6d70}
	.insEmpty{color:#6a6d70;font-size:13px}
	.insLog{font:12px/1.5 ui-monospace,monospace;word-break:break-all;border-bottom:1px dashed #eee;padding:4px 0}
	.insLog .m{display:inline-block;min-width:44px;font-weight:700;color:#107e3e}
	body.insOn *{cursor:help !important}
	@media (prefers-color-scheme: dark){.insPanel{background:#1d232a;color:#e6e9ec;border-color:#333}.insRow{border-color:#333}.insPath span{background:#2a313a}.insHead,.insTabs{border-color:#333}.insHead button,.insTabs button{background:#1d232a;color:#e6e9ec;border-color:#444}.insBtn{background:#1d232a}}
	`;

	const esc = (s) => String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "\"": "&quot;" }[c]));
	const byId = (id) => (Element.getElementById ? Element.getElementById(id) : Element.registry.get(id));

	function entityOf(fullPath) {
		const segs = fullPath.split("/").filter(Boolean);
		segs.pop(); // 마지막은 속성 이름
		for (let i = segs.length - 1; i >= 0; i--) {
			const s = segs[i].replace(/\(.*\)$/, "");
			if (ENTITY[s]) { return ENTITY[s]; }
		}
		return null;
	}
	function sapField(fullPath) {
		const prop = fullPath.split("/").pop();
		const ent = entityOf(fullPath);
		if (ent && FIELDMAP[ent] && FIELDMAP[ent][prop]) { return FIELDMAP[ent][prop]; }
		for (const k in FIELDMAP) { if (FIELDMAP[k][prop]) { return FIELDMAP[k][prop]; } }
		return null;
	}
	function shortName(c) { return c.getMetadata().getName().replace(/^sap\.(m|f|uxap|ui\.table|ui\.layout\.form|ui\.core\.mvc)\./, (m, p) => ({ m: "m.", f: "f.", uxap: "uxap.", "ui.table": "table.", "ui.layout.form": "form.", "ui.core.mvc": "mvc." }[p])); }
	function hasBinding(c) {
		return BOUND_PROPS.some((p) => c.getBindingInfo && c.getMetadata().getProperty(p) && c.getBindingInfo(p)) ||
			["items", "rows"].some((a) => c.getBindingInfo && c.getBindingInfo(a));
	}

	const Inspector = {
		_on: false, _log: [], _comp: null, _sel: null, _tab: "ctrl",

		attach(oComponent) {
			if (window.__gaonInspector) { window.__gaonInspector._comp = oComponent; window.__gaonInspector._watchModels(); return; }
			window.__gaonInspector = this;
			this._comp = oComponent;
			const st = document.createElement("style"); st.textContent = css; document.head.appendChild(st);
			this._btn = Object.assign(document.createElement("button"), { className: "insBtn", type: "button", textContent: "구성 보기" });
			this._btn.title = "화면이 어떤 컨트롤과 데이터로 만들어졌는지 봅니다";
			this._hl = Object.assign(document.createElement("div"), { className: "insHl" });
			this._selBox = Object.assign(document.createElement("div"), { className: "insSel" });
			this._tag = Object.assign(document.createElement("div"), { className: "insTag" });
			this._panel = Object.assign(document.createElement("aside"), { className: "insPanel" });
			this._panel.innerHTML = `<div class="insHead"><span>구성 보기</span><button type="button" data-a="close">닫기</button></div>
				<div class="insTabs"><button type="button" data-t="ctrl" aria-pressed="true">선택한 컨트롤</button><button type="button" data-t="model" aria-pressed="false">모델</button><button type="button" data-t="log" aria-pressed="false">OData 요청</button></div>
				<div class="insBody"></div>`;
			document.body.append(this._btn, this._hl, this._selBox, this._tag, this._panel);
			this._btn.addEventListener("click", () => this.toggle());
			this._panel.addEventListener("click", (e) => {
				const t = e.target.closest("[data-t]"); if (t) { this._tab = t.dataset.t; this._render(); }
				if (e.target.closest("[data-a=close]")) { this.toggle(false); }
			});
			document.addEventListener("mouseover", (e) => this._hover(e), true);
			document.addEventListener("click", (e) => this._click(e), true);
			// 구성 보기 중에는 앱이 누름(tap/press)을 받지 않게 막는다
			["mousedown", "mouseup", "pointerdown", "pointerup", "touchstart", "touchend"].forEach((ev) => document.addEventListener(ev, (e) => {
				if (this._on && !e.target.closest(".insPanel,.insBtn")) { e.stopPropagation(); }
			}, true));
			document.addEventListener("keydown", (e) => { if (this._on && e.key === "Escape") { this.toggle(false); } }, true);
			window.addEventListener("scroll", () => this._place(this._selBox, this._sel), true);
			this._watchModels();
		},

		_watchModels() {
			const c = this._comp; if (!c) { return; }
			const names = [undefined].concat(Object.keys(c.oModels || {}).filter((n) => n !== "undefined"));
			names.forEach((n) => {
				const m = c.getModel(n);
				if (m && m.isA && m.isA("sap.ui.model.odata.v2.ODataModel") && !m.__insWatched) {
					m.__insWatched = true;
					m.attachRequestCompleted((e) => {
						this._log.unshift({ method: e.getParameter("method"), url: decodeURIComponent(e.getParameter("url") || ""), ok: e.getParameter("success"), t: new Date().toLocaleTimeString() });
						this._log.length = Math.min(this._log.length, 60);
						if (this._on && this._tab === "log") { this._render(); }
					});
				}
			});
		},

		toggle(force) {
			this._on = typeof force === "boolean" ? force : !this._on;
			this._btn.classList.toggle("on", this._on);
			this._btn.textContent = this._on ? "구성 보기 끄기" : "구성 보기";
			document.body.classList.toggle("insOn", this._on);
			this._panel.classList.toggle("open", this._on);
			if (!this._on) { [this._hl, this._selBox, this._tag].forEach((d) => { d.style.display = "none"; }); this._sel = null; }
			this._render();
		},

		_controlAt(target) {
			if (!target || target.closest(".insPanel,.insBtn")) { return null; }
			const el = target.closest("[data-sap-ui]");
			const start = el && byId(el.getAttribute("data-sap-ui") || el.id);
			// 1) 가까운 조상(4단계 안)에 바인딩이 있는 컨트롤이 있으면 그것 (ObjectIdentifier 안쪽 글자 → ObjectIdentifier)
			// 2) 없으면 설명이 있는 첫 컨트롤 (표 머리글 → Column, 제목 → Title)
			let c = start, n = 0, firstDoc = null;
			while (c && n < 12) {
				if (c.getMetadata) {
					if (n <= 4 && hasBinding(c)) { return c.getDomRef ? c : null; }
					if (!firstDoc && CONTROL_DOC[c.getMetadata().getName()]) { firstDoc = c; }
				}
				c = c.getParent && c.getParent(); n++;
			}
			return firstDoc && firstDoc.getDomRef ? firstDoc : null;
		},
		_place(box, c) {
			const d = c && c.getDomRef && c.getDomRef();
			if (!d || !this._on) { box.style.display = "none"; return null; }
			const r = d.getBoundingClientRect();
			Object.assign(box.style, { display: "block", left: r.left + "px", top: r.top + "px", width: r.width + "px", height: r.height + "px" });
			return r;
		},
		_hover(e) {
			if (!this._on) { return; }
			const c = this._controlAt(e.target);
			const r = this._place(this._hl, c);
			if (r) { Object.assign(this._tag.style, { display: "block", left: r.left + "px", top: Math.max(0, r.top - 18) + "px", height: "auto", width: "auto" }); this._tag.textContent = shortName(c); } else { this._tag.style.display = "none"; }
		},
		_click(e) {
			if (!this._on || e.target.closest(".insPanel,.insBtn")) { return; }
			e.preventDefault(); e.stopPropagation();
			const c = this._controlAt(e.target);
			if (!c) { return; }
			this._sel = c; this._tab = "ctrl";
			this._place(this._selBox, c);
			this._render();
		},

		_render() {
			if (!this._panel) { return; }
			this._panel.querySelectorAll("[data-t]").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.t === this._tab)));
			const body = this._panel.querySelector(".insBody");
			body.innerHTML = this._tab === "model" ? this._htmlModels() : this._tab === "log" ? this._htmlLog() : this._htmlControl();
		},

		_htmlControl() {
			const c = this._sel;
			if (!c) { return `<p class="insEmpty">화면에서 아무 곳이나 누르면 그 컨트롤의 정체가 여기에 나옵니다. 앱 동작(이동·검색)은 구성 보기를 끄면 다시 됩니다.</p>`; }
			const name = c.getMetadata().getName();
			let h = `<div class="insCls">${esc(name)}</div><p>${esc(CONTROL_DOC[name] || "UI5 컨트롤입니다.")}</p>`;
			const id = c.getId();
			const view = c.getParent && (function up(x) { while (x && !(x.isA && x.isA("sap.ui.core.mvc.View"))) { x = x.getParent(); } return x; })(c);
			const local = view && id.startsWith(view.getId() + "--") ? id.slice(view.getId().length + 2) : "";
			h += `<div class="insNote">ID: <code>${esc(local ? local : id)}</code>${local ? " (뷰 XML의 id) · 컨트롤러에서 this.byId(\"" + esc(local) + "\")" : " (자동 생성 ID)"}</div>`;
			if (view) { h += `<div class="insNote">뷰: <code>${esc(view.getViewName ? view.getViewName() : "")}</code></div>`; }
			// 부모 경로
			const chain = []; let p = c.getParent(); let k = 0;
			while (p && k < 30) { const nm = p.getMetadata && p.getMetadata().getName(); if (nm && CONTROL_DOC[nm]) { chain.unshift(shortName(p)); } p = p.getParent && p.getParent(); k++; }
			h += `<h4>화면 안의 위치 (바깥 → 안)</h4><div class="insPath">${chain.concat(shortName(c)).map((x) => `<span>${esc(x)}</span>`).join("<span>›</span>")}</div>`;
			// 요소 바인딩 (bindElement)
			const eb = c.getElementBinding && c.getElementBinding();
			if (eb) { h += `<h4>bindElement</h4><div class="insRow"><code>${esc(eb.getPath())}</code><span class="insNote">이 컨트롤 아래의 상대 경로 바인딩은 모두 이 경로를 기준으로 읽습니다.</span></div>`; }
			// 집합 바인딩
			["items", "rows"].forEach((a) => {
				const bi = c.getBindingInfo(a); if (!bi) { return; }
				const b = c.getBinding(a);
				const ctx = b && b.getContext && b.getContext();
				const full = bi.path && !bi.path.startsWith("/") && ctx ? ctx.getPath() + "/" + bi.path : bi.path;
				const tmpl = bi.template ? shortName(bi.template) : "";
				h += `<h4>목록 바인딩 (${a})</h4><div class="insRow"><b>경로</b><code>${esc((bi.model ? bi.model + ">" : "") + bi.path)}</code>${full !== bi.path ? `<b>전체 경로</b><code>${esc(full)}</code>` : ""}
					<b>현재 건수</b><span>${b ? b.getLength() : "-"}건${b && b.isA && b.isA("sap.ui.model.odata.v2.ODataListBinding") ? " (서버가 알려준 전체 건수)" : ""}</span>
					${tmpl ? `<b>템플릿</b><span><code>${esc(tmpl)}</code>를 건수만큼 복제해 한 줄씩 만듭니다.</span>` : ""}${bi.model && AUX[bi.model] ? `<span class="insNote">${esc(AUX[bi.model])}</span>` : ""}</div>`;
			});
			// 속성 바인딩
			const rows = [];
			BOUND_PROPS.forEach((prop) => {
				if (!c.getMetadata().getProperty(prop)) { return; }
				const bi = c.getBindingInfo(prop); if (!bi) { return; }
				const parts = bi.parts || [{ path: bi.path, model: bi.model }];
				const val = c.getProperty(prop);
				let r = `<div class="insRow"><b>${esc(prop)}</b><span>화면 값: <code>${esc(typeof val === "object" ? JSON.stringify(val) : val)}</code></span>`;
				parts.forEach((pt) => {
					if (!pt || pt.path === undefined) { return; }
					const ctx = c.getBindingContext(pt.model);
					const full = pt.path.startsWith("/") || !ctx ? pt.path : ctx.getPath() + "/" + pt.path;
					const f = (!pt.model || pt.model === "acc" || pt.model === "doc") ? sapField(full) : null;
					r += `<span>바인딩: <code>{${esc((pt.model ? pt.model + ">" : "") + pt.path)}}</code></span>`;
					if (full !== pt.path) { r += `<span class="insNote">전체 경로: <code>${esc(full)}</code></span>`; }
					if (f) { r += `<span>SAP 저장 위치: <span class="insSap">${esc(f.t)}</span> ${esc(f.ko)}</span>`; }
					if (pt.model && AUX[pt.model]) { r += `<span class="insNote">${esc(AUX[pt.model])}</span>`; }
					if (pt.path.startsWith("_")) { r += `<span class="insNote">밑줄로 시작하는 값은 실제 API에 없는 교육용 요약입니다.</span>`; }
				});
				const b = c.getBinding(prop);
				const type = b && b.getType && b.getType();
				if (type) { r += `<span class="insNote">타입: <code>${esc(type.getMetadata().getName())}</code> — 값을 화면 형식으로 바꿉니다.</span>`; }
				if (bi.formatter) { r += `<span class="insNote">formatter 함수가 값을 바꿔서 보여줍니다 (model/formatter.js).</span>`; }
				rows.push(r + "</div>");
			});
			h += rows.length ? `<h4>속성 바인딩</h4>${rows.join("")}` : (c.getBindingInfo("items") || c.getBindingInfo("rows") ? "" : `<h4>속성 바인딩</h4><p class="insEmpty">이 컨트롤은 데이터에 묶여 있지 않습니다 (고정 글자 또는 틀).</p>`);
			return h;
		},

		_htmlModels() {
			const c = this._comp; if (!c) { return ""; }
			const ds = c.getManifestEntry("/sap.app/dataSources") || {};
			const models = c.getManifestEntry("/sap.ui5/models") || {};
			let h = `<p class="insNote">manifest.json의 <code>sap.app/dataSources</code>(데이터가 어디 있는지)와 <code>sap.ui5/models</code>(그 데이터를 어떤 모델로 만들지)입니다.</p>`;
			Object.keys(models).forEach((n) => {
				const m = models[n]; const d = m.dataSource && ds[m.dataSource];
				const inst = c.getModel(n === "" ? undefined : n);
				h += `<div class="insRow"><b>${n === "" ? "기본 모델 (이름 없음)" : "모델 " + esc(n)}</b><span><code>${esc(inst ? inst.getMetadata().getName() : m.type || "")}</code></span>
					${d ? `<span>dataSource <code>${esc(m.dataSource)}</code> → <code>${esc(d.uri)}</code> (${esc(d.type || "")}${d.settings && d.settings.odataVersion ? " " + esc(d.settings.odataVersion) : ""})</span>` : ""}
					${m.uri ? `<span>uri <code>${esc(m.uri)}</code></span>` : ""}${AUX[n] ? `<span class="insNote">${esc(AUX[n])}</span>` : ""}</div>`;
			});
			return h;
		},

		_htmlLog() {
			const c = this._comp;
			const hasOData = c && c.getModel() && c.getModel().isA && c.getModel().isA("sap.ui.model.odata.v2.ODataModel");
			if (!hasOData) { return `<p class="insEmpty">이 앱은 JSONModel이라 서버에 묻지 않습니다. JSON 파일을 처음에 한 번 통째로 받고, 검색·정렬은 브라우저 안에서 합니다.</p><p class="insNote">OData 앱에서는 여기에 화면이 서버에 보낸 요청($filter, $top, $skip …)이 쌓입니다.</p>`; }
			if (!this._log.length) { return `<p class="insEmpty">아직 요청이 없습니다.</p>`; }
			return `<p class="insNote">화면이 서버(여기서는 MockServer)에 보낸 OData 요청입니다. 검색하거나 스크롤해 보세요.</p>` +
				this._log.map((l) => `<div class="insLog"><span class="m">${esc(l.method)}</span>${esc(l.url.replace(/^.*\/sap\/opu\/odata\/sap\/[A-Z_]+\//, ""))}<br><span class="insNote">${esc(l.t)} · ${l.ok ? "성공" : "실패"}</span></div>`).join("");
		}
	};
	return Inspector;
});
