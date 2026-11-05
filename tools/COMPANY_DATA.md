# 가상 회사 데이터 (schema `sap-edu-company/1`)

이 페이지의 모든 화면은 `data/<회사>.json` 하나에서 계산합니다. 다른 회사를 추가하려면:

1. `tools/generate_company.py`의 CONFIG(회사·플랜트·조직 코드), 자재·BOM·라우팅, 고객·공급업체, G/L 계정 목록을 바꿉니다.
2. `python3 tools/generate_company.py course/data/<id>.json` → 지정한 경로에 생성. 모든 전표 차변=대변, 재고·채권·채무 잔액 일치를 검사한 뒤 저장합니다. 같은 seed면 같은 데이터.
3. `course/data/companies.json`에 한 줄 추가합니다. 화면 오른쪽 위 회사 버튼에서 바꿀 수 있습니다.

## 파일 구조

| 키 | 내용 |
|---|---|
| `company` | id, name, industry, bukrs, kokrs, ktopl, waers, fx, period[시작, 끝], opening, vat, seed, plants{코드: 이름} |
| `tables` | `{테이블: {module, desc, kind(org/master/trans), cds, virtual, fields[], rows[[...]]}}` (SAP 필드 이름 그대로) |
| `flow` | `[[앞 문서 유형, 번호, 뒤 문서 유형, 번호]]` 문서 흐름 (VBAK→LIKP→MATDOC/VBRK→BKPF…) |
| `events` | `{역 id: {날짜: 건수}}` 노선도 타임라인 재생용 |
| `featured` | 노선도·화면 설명에 쓰는 대표 문서 (so, dlv, pgi, bil, pay, pro, mrp, po, gr, iv, payout, je, dep, alloc, kostl) |
| `openItems` | 기간 끝 미결 채권(ar: DUE=지급조건 만기일)·채무(ap) |
| `std`, `stock`, `gl` | 표준원가, 기간 끝 재고, G/L 계정 이름·유형(X/P/S)·원가요소 범주 |

화면 문구는 `{so.no}`, `{po.mat|won}` 같은 템플릿으로 `featured`를 읽으므로 회사가 바뀌어도 문구를 고칠 필요가 없습니다. 템플릿 뒤 조사(을/를, 이/가, 은/는, 으로/로, 과/와)는 값에 맞춰 자동으로 바뀝니다.

교육용 뷰 `BSE_CLR`(반제 기록), `JEST_TXT`(오더 상태 텍스트), `SETTLE`(정산 결과)은 실제 SAP 테이블 이름이 아닙니다.

## 앱 데이터

`apps/` 의 앱들은 `course/data/gaon.json`에서 뽑은 데이터를 씁니다. 회사 데이터를 다시 만들었다면 `python3 tools/extract_app_data.py`로 앱 데이터도 다시 만드세요.
