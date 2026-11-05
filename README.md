# SAP S/4HANA 모듈 코스 + 실행해 보는 Fiori 앱

가상 제조사 **가온전자(주)** 의 석 달치 SAP 데이터(판매오더 237건, 회계 라인 8,421줄 등)를 바탕으로 만든 자습 자료입니다.

- **코스**: S/4HANA 모듈(SD·MM·PP·FI·CO)이 어떻게 이어지는지 12장 60단계로 순서대로 봅니다.
- **앱 4개**: 같은 데이터로 실제 동작하는 SAPUI5 앱입니다. 화면이 어떤 컨트롤과 데이터로 만들어지는지 직접 열어 볼 수 있습니다.

기준: SAP S/4HANA 온프레미스/Private Edition 2023 이후, SAPUI5/OpenUI5 1.120.

## 들어 있는 것

| 폴더 | 내용 | 눈여겨볼 UI5 기능 |
|---|---|---|
| `course/` | 12장 60단계 코스 페이지 (`index.html` 하나 + `data/`) | — |
| `apps/so-json/` | 판매오더 관리 **(a) JSONModel** | DynamicPage, sap.m.Table, ObjectPageLayout, Fragment 팝업 |
| `apps/so-odata/` | 판매오더 관리 **(b) OData V2 + MockServer** | ODataModel, `$filter`·`$top`, 내비게이션 속성 |
| `apps/bp/` | 비즈니스 파트너 조회 | FlexibleColumnLayout(목록-상세 2열), 조건부 섹션 |
| `apps/je/` | 분개 조회 (ACDOCA) | sap.ui.table.Table(8천 줄), Fragment 팝업, 합계 계산 |
| `launchpad/` | 웹에서 앱 4개와 코스를 한 화면에서 여는 런치패드 | ComponentContainer, ShellBar, GenericTile |
| `shared/ext/Inspector.js` | 모든 앱에 들어간 **구성 보기** 기능의 원본 | — |
| `tools/` | 회사 데이터 생성기, 앱 데이터 추출, 공통 파일 복사 스크립트 | — |

앱 폴더는 수업 프로젝트와 같은 Fiori 도구 기본 구조입니다: `package.json`, `ui5.yaml`, `ui5-local.yaml`, `webapp/`(manifest.json, Component.js, view, controller, i18n, model).

## 실행하기

### 앱 하나를 수업처럼 실행

```bash
cd apps/so-json        # so-odata, bp, je 도 같음
npm install
npm start              # Fiori 런치패드 미리보기. UI5는 ui5.sap.com에서 받음
npm run start-local    # SAPUI5 1.120.2를 npm에서 받아서 실행 (처음엔 내려받느라 몇 분 걸림)
npm run start-noflp    # 런치패드 없이 index.html로 바로
```

BAS(SAP Business Application Studio)에서도 터미널에서 같은 명령을 쓰면 됩니다.

### 웹으로 전체 보기 (런치패드)

레포 폴더를 정적 웹 서버로 열고 `/launchpad/`로 들어갑니다. UI5는 OpenUI5 CDN(`sdk.openui5.org/1.120`)에서 불러옵니다.

```bash
npx http-server . -p 8080        # 또는: python -m http.server 8080
# 브라우저: http://localhost:8080/launchpad/
```

GitHub Pages로 올리면 링크 하나로 볼 수 있습니다. 레포가 공개여야 무료로 쓸 수 있습니다.

1. Settings → General 맨 아래 "Change visibility"에서 Public으로 바꿉니다.
2. Settings → Pages에서 Branch를 `main` / `/ (root)`로 정하고 Save를 누릅니다.
3. 몇 분 뒤 `https://ldh106.github.io/sap-s4hana-module-course/launchpad/`로 들어갑니다. 코스는 `.../course/`에 있습니다.

## 구성 보기

각 앱 오른쪽 아래 **구성 보기** 버튼을 켜고 화면 아무 곳이나 누르면, 앱 동작 대신 그 부분의 정체를 오른쪽 패널에 보여줍니다.

- **컨트롤**: `sap.m.ObjectIdentifier`처럼 무슨 컨트롤인지, 어떤 역할인지 보여줍니다.
- **화면 안의 위치**: `ObjectPageLayout › ObjectPageSection › Table › ColumnListItem`처럼 부모부터 이어서 보여줍니다.
- **바인딩**: `{Material}`과 같은 경로가 실제로는 `/A_SalesOrder/39/to_Item/0/Material`이고, 지금 화면 값이 무엇인지 보여줍니다.
- **SAP 저장 위치**: 그 값이 SAP의 어느 테이블-필드(`VBAP-MATNR 자재`)에 저장되는지 보여줍니다.
- **모델 탭**: manifest.json의 dataSources와 models를 보여줍니다. 데이터가 어디서 어떤 모델로 들어오는지 확인할 수 있습니다.
- **OData 요청 탭** ((b) 앱): 화면이 서버에 보낸 요청을 보여줍니다. 예: `A_SalesOrder?$skip=0&$top=30&$filter=...`

## (a) JSONModel과 (b) OData는 무엇이 다른가

화면(XML 뷰)은 네임스페이스(`gaon.sojson` / `gaon.soodata`)와 날짜 타입만 빼고 같습니다. 데이터를 가져오는 방법만 다릅니다. 코드에서 `[JSON]` · `[OData]` 주석이 붙은 곳이 차이 나는 부분입니다.

| 위치 | (a) JSONModel | (b) OData V2 |
|---|---|---|
| `manifest.json` dataSources | `model/salesOrders.json` (type JSON) | `/sap/opu/odata/sap/API_SALES_ORDER_SRV/` (type OData 2.0) |
| `Component.js` | `setSizeLimit(1000)`: JSONModel은 목록을 기본 100건까지만 보여줌 | `mockserver.init()`: 진짜 서버 대신 브라우저 안 가짜 서버를 켬 |
| 데이터를 받는 시점 | 시작할 때 파일 하나를 통째로 | 필요할 때 필요한 만큼 (`$top=30`, 스크롤하면 더) |
| 검색 (같은 Filter 코드) | 브라우저 안에서 거름 | `$filter=substringof(...)` URL로 서버에 감 |
| 상세 화면 경로 | `/A_SalesOrder/39` (배열 위치) | `/A_SalesOrder('10000040')` (키, `createKey`) |
| 아이템 `to_Item` | 판매오더 객체 안의 배열 | 내비게이션 속성 → 요청이 따로 나감 |
| 날짜 | 문자열 `"2026-08-11"` → `type.Date` + source pattern | `Edm.DateTime` → `odata.type.DateTime` |

실무 S/4HANA 앱은 (b)처럼 OData 서비스를 씁니다. (b)에서 `localService/`와 `mockserver.init()`만 빼면 진짜 서버에 붙는 구조입니다.

## 데이터와 정확성

- 회사·고객·금액은 모두 가상입니다. `tools/generate_company.py`로 만들고, 모든 전표의 차변 합계와 대변 합계가 같은지 검사했습니다.
- 앱의 속성 이름은 실제 API와 같습니다. 판매오더는 `API_SALES_ORDER_SRV`의 `A_SalesOrder`·`A_SalesOrderItem`·`A_SalesOrderSubsqntProcFlow`, BP는 `API_BUSINESS_PARTNER`의 `A_BusinessPartner` 구조입니다. SAP Cloud SDK에 들어 있는 서비스 정의로 이름과 타입을 확인했습니다. `metadata.xml`은 이 앱이 쓰는 속성만 남긴 일부입니다.
- 실제 API에 없지만 교육용으로 덧붙인 것은 화면에 따로 표시했습니다.
  - 판매오더의 회계 전표(`acc` 모델)
  - BP의 거래 요약(`_stats`)
  - 코드 이름(`texts.json`)
- 분개 조회는 ACDOCA 필드 이름을 SE16N처럼 그대로 씁니다. 표준 API인 `API_JOURNALENTRYITEMBASIC_SRV`는 전표 번호가 없는 집계용이라 이 화면에는 맞지 않아 쓰지 않았습니다.
- 처리 상태 A/B/C는 미처리 / 처리 중 / 완료입니다. 후속 문서 범주는 J 출하, R 재고 이동, M 청구입니다.
- SAP GUI 화면(VA01 등)은 코스 페이지에서 HTML로 흉내 낸 것입니다. 이 레포는 실제 SAP 시스템에 연결되지 않습니다.

## 데이터나 공통 파일을 바꿨을 때

```bash
python3 tools/extract_app_data.py   # course/data/gaon.json → 각 앱 model/, localService/mockdata/
python3 tools/sync_shared.py        # shared/ext/Inspector.js → 각 앱 webapp/ext/
```

다른 가상 회사를 만드는 방법은 `tools/COMPANY_DATA.md`에 있습니다.

## 참고한 자료

- SAP Cloud SDK 서비스 정의 (npm): `@sap/cloud-sdk-vdm-sales-order-service`, `@sap/cloud-sdk-vdm-business-partner-service`, `@sap/cloud-sdk-vdm-journal-entry-item-basic-service` (2.1.0)
- [SAP Learning – Working with Business Partners in SAP S/4HANA](https://learning.sap.com/learning-journeys/exploring-functions-and-innovation-in-sap-s-4hana-sourcing-and-procurement/working-with-business-partners-in-sap-s-4hana_fbf39423-74f9-4851-bf8b-6a79ebd8cb73) (FLVN00 · FLVN01)
- [SAP Community – S/4HANA Business Partner, BP to Customer, BP to Vendor, CVI](https://blogs.sap.com/2018/04/10/s4hana-business-partner-bp-to-customer-bp-to-vendor-bp-to-cvi/) (FLCU00 · FLCU01)
- [UI5 문서 – Variant for Bootstrapping from Content Delivery Network](https://ui5.github.io/docs/04_Essentials/variant-for-bootstrapping-from-content-delivery-network-2d3eb2f.html) (OpenUI5 CDN 주소)

SAP, S/4HANA, Fiori, SAPUI5는 SAP SE의 상표이며, 이 자료는 SAP와 관련이 없습니다. UI5 라이브러리는 이 레포에 들어 있지 않고 실행할 때 npm이나 CDN에서 받습니다.
