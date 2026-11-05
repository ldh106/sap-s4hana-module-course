#!/usr/bin/env python3
"""가온전자 회사 데이터(course/data/gaon.json)를 각 UI5 앱이 쓰는 데이터로 변환한다.

실행: python3 tools/extract_app_data.py   (레포 루트에서)

만드는 파일
  apps/so-json/webapp/model/salesOrders.json      (a) JSONModel용. 속성 이름은 API_SALES_ORDER_SRV와 같게
  apps/so-odata/webapp/localService/mockdata/*.json (b) MockServer용. 엔터티 세트마다 파일 하나
  apps/so-*/webapp/model/customers.json, accounting.json   두 앱이 같이 쓰는 보조 데이터
  apps/bp/webapp/model/businessPartners.json       API_BUSINESS_PARTNER 구조를 흉내 낸 JSON
  apps/je/webapp/model/acdoca.json                 ACDOCA 라인 (SE16N처럼 테이블 필드 이름 그대로)
  launchpad/tiles.json                             런치패드 타일 숫자
"""
import json, os, uuid, datetime, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'course', 'data', 'gaon.json')
D = json.load(open(SRC, encoding='utf-8'))
T = D['tables']


def rows(name):
    t = T[name]
    return [dict(zip(t['fields'], r)) for r in t['rows']]


def write(rel, obj, compact=False):
    p = os.path.join(ROOT, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'w', encoding='utf-8') as f:
        if compact:
            json.dump(obj, f, ensure_ascii=False, separators=(',', ':'))
        else:
            json.dump(obj, f, ensure_ascii=False, indent=1)
    print(f'{rel}: {os.path.getsize(p):,} bytes')


def odate(s):
    """OData V2 JSON의 Edm.DateTime 표기: /Date(밀리초)/ (UTC 자정)"""
    d = datetime.datetime.strptime(s, '%Y-%m-%d').replace(tzinfo=datetime.timezone.utc)
    return f'/Date({int(d.timestamp() * 1000)})/'


def num(v):
    """Edm.Decimal은 JSON에서 문자열로 온다"""
    return str(int(v)) if float(v).is_integer() else str(v)


FLOW = collections.defaultdict(list)
for a, ak, b, bk in D['flow']:
    FLOW[(a, ak)].append((b, bk))

VBAK, VBAP, LIKP, VBRK, VBRP = rows('VBAK'), rows('VBAP'), {r['VBELN']: r for r in rows('LIKP')}, {r['VBELN']: r for r in rows('VBRK')}, rows('VBRP')
BKPF = {r['BELNR']: r for r in rows('BKPF')}
MATDOC = collections.defaultdict(list)
for r in rows('MATDOC'):
    MATDOC[r['MBLNR']].append(r)
ACD = rows('ACDOCA')
ACD_BY_DOC = collections.defaultdict(list)
for r in ACD:
    ACD_BY_DOC[r['BELNR']].append(r)
KNA1 = {r['KUNNR']: r for r in rows('KNA1')}
LFA1 = {r['LIFNR']: r for r in rows('LFA1')}
GL = {k: v['n'] for k, v in D['gl'].items()}

items_by_so = collections.defaultdict(list)
for r in VBAP:
    items_by_so[r['VBELN']].append(r)
billed_items = {(r['AUBEL'], r['AUPOS']) for r in VBRP}


def bill_status(so):
    its = items_by_so[so]
    n = sum(1 for i in its if (so, i['POSNR']) in billed_items)
    return 'A' if n == 0 else ('C' if n == len(its) else 'B')


def subsequent(so):
    """판매오더 → 출하(J) → 재고 이동(R) · 청구(M). VBFA 후속 문서 범주 코드"""
    out = []
    for t, k in FLOW[('VBAK', so)]:
        if t != 'LIKP':
            continue
        out.append(('J', k, LIKP[k]['ERDAT']))
        for t2, k2 in FLOW[('LIKP', k)]:
            if t2 == 'MATDOC':
                out.append(('R', k2, MATDOC[k2][0]['BUDAT']))
            elif t2 == 'VBRK':
                out.append(('M', k2, VBRK[k2]['FKDAT']))
    return out


def accounting(so):
    """교육용 보조 데이터: 판매오더 하나에서 이어진 회계 전표 (API_SALES_ORDER_SRV에는 없음)"""
    out = []
    for t, k in FLOW[('VBAK', so)]:
        for t2, k2 in FLOW[('LIKP', k)]:
            for t3, k3 in FLOW[(t2, k2)]:
                if t3 != 'BKPF':
                    continue
                kind = '출고 · 매출원가' if t2 == 'MATDOC' else '청구 · 매출과 채권'
                out.append((kind, k3, t2, k2))
                for t4, k4 in FLOW[('BKPF', k3)]:
                    out.append(('입금 · 채권 반제', k4, 'BKPF', k3))
    res = []
    for kind, belnr, rt, rk in out:
        h = BKPF.get(belnr, {})
        lines = ACD_BY_DOC.get(belnr, [])
        res.append({'kind': kind, 'BELNR': belnr, 'BLART': h.get('BLART', ''), 'BUDAT': h.get('BUDAT', ''),
                    'amount': sum(l['HSL'] for l in lines if l['DRCRK'] == 'S'), 'currency': 'KRW',
                    'refType': rt, 'ref': rk, 'text': h.get('BKTXT', ''),
                    'lines': [{'RACCT': l['RACCT'], 'name': GL.get(l['RACCT'], ''), 'DRCRK': l['DRCRK'], 'HSL': l['HSL']} for l in lines]})
    return res


# ───────── (a) JSON: 판매오더 ─────────
so_json, acc_json = [], {}
mock_so, mock_item, mock_flow = [], [], []
for h in VBAK:
    so = h['VBELN']
    head = {
        'SalesOrder': so, 'SalesOrderType': h['AUART'], 'SalesOrganization': h['VKORG'],
        'DistributionChannel': h['VTWEG'], 'OrganizationDivision': h['SPART'], 'SoldToParty': h['KUNNR'],
        'CreationDate': h['ERDAT'], 'SalesOrderDate': h['AUDAT'], 'PurchaseOrderByCustomer': h['BSTNK'],
        'RequestedDeliveryDate': h['VDATU'], 'TotalNetAmount': h['NETWR'], 'TransactionCurrency': h['WAERK'],
        'CustomerPaymentTerms': h['ZTERM'], 'IncotermsClassification': h['INCO1'],
        'OverallSDProcessStatus': h['GBSTK'], 'OverallDeliveryStatus': h['LFSTK'],
    }
    its = [{
        'SalesOrder': so, 'SalesOrderItem': i['POSNR'], 'SalesOrderItemCategory': i['PSTYV'], 'SalesOrderItemText': i['ARKTX'],
        'Material': i['MATNR'], 'RequestedQuantity': i['KWMENG'], 'RequestedQuantityUnit': i['VRKME'],
        'NetAmount': i['NETWR'], 'TransactionCurrency': i['WAERK'], 'ProductionPlant': i['WERKS'], 'SDProcessStatus': i['GBSTA'],
    } for i in items_by_so[so]]
    flow = [{'SalesOrder': so, 'DocRelationshipUUID': str(uuid.uuid5(uuid.NAMESPACE_URL, f'gaon/{so}/{doc}')),
             'SubsequentDocument': doc, 'SubsequentDocumentCategory': cat, 'CreationDate': dt} for cat, doc, dt in subsequent(so)]
    so_json.append({**head, 'to_Item': its, 'to_SubsequentProcFlowDoc': flow})
    acc = accounting(so)
    if acc:
        acc_json[so] = acc
    # (b) OData mockdata: 날짜는 /Date()/, 금액·수량은 문자열
    mock_so.append({**head, 'CreationDate': odate(head['CreationDate']), 'SalesOrderDate': odate(head['SalesOrderDate']),
                    'RequestedDeliveryDate': odate(head['RequestedDeliveryDate']), 'TotalNetAmount': num(head['TotalNetAmount'])})
    mock_item += [{**i, 'RequestedQuantity': num(i['RequestedQuantity']), 'NetAmount': num(i['NetAmount'])} for i in its]
    mock_flow += [{**f, 'CreationDate': odate(f['CreationDate'])} for f in flow]

customers = {k: {'name': v['NAME1'], 'city': v['ORT01'], 'country': v['LAND1']} for k, v in KNA1.items()}
write('apps/so-json/webapp/model/salesOrders.json', {'A_SalesOrder': so_json})
for app in ('so-json', 'so-odata'):
    write(f'apps/{app}/webapp/model/customers.json', customers)
    write(f'apps/{app}/webapp/model/accounting.json', acc_json, compact=True)
write('apps/so-odata/webapp/localService/mockdata/A_SalesOrder.json', mock_so)
write('apps/so-odata/webapp/localService/mockdata/A_SalesOrderItem.json', mock_item)
write('apps/so-odata/webapp/localService/mockdata/A_SalesOrderSubsqntProcFlow.json', mock_flow)

# ───────── BP: API_BUSINESS_PARTNER 모양 ─────────
roles = collections.defaultdict(list)
for r in rows('BUT100'):
    roles[r['PARTNER']].append({'BusinessPartner': r['PARTNER'], 'BusinessPartnerRole': r['RLTYP']})
knb1 = collections.defaultdict(list); knvv = collections.defaultdict(list); lfb1 = collections.defaultdict(list); lfm1 = collections.defaultdict(list)
for r in rows('KNB1'): knb1[r['KUNNR']].append({'Customer': r['KUNNR'], 'CompanyCode': r['BUKRS'], 'ReconciliationAccount': r['AKONT'], 'PaymentTerms': r['ZTERM']})
for r in rows('KNVV'): knvv[r['KUNNR']].append({'Customer': r['KUNNR'], 'SalesOrganization': r['VKORG'], 'DistributionChannel': r['VTWEG'], 'Division': r['SPART'], 'Currency': r['WAERS'], 'CustomerPaymentTerms': r['ZTERM'], 'IncotermsClassification': r['INCO1'], 'CustomerGroup': r['KDGRP']})
for r in rows('LFB1'): lfb1[r['LIFNR']].append({'Supplier': r['LIFNR'], 'CompanyCode': r['BUKRS'], 'ReconciliationAccount': r['AKONT'], 'PaymentTerms': r['ZTERM']})
for r in rows('LFM1'): lfm1[r['LIFNR']].append({'Supplier': r['LIFNR'], 'PurchasingOrganization': r['EKORG'], 'PurchaseOrderCurrency': r['WAERS'], 'PaymentTerms': r['ZTERM']})
so_cnt = collections.Counter(h['KUNNR'] for h in VBAK); so_amt = collections.Counter()
for h in VBAK:
    so_amt[h['KUNNR']] += h['NETWR'] if h['WAERK'] == 'KRW' else 0
po = rows('EKKO'); po_cnt = collections.Counter(r['LIFNR'] for r in po); po_amt = collections.Counter()
for r in po:
    po_amt[r['LIFNR']] += r['NETWR']
open_ar = collections.Counter()
for r in D.get('openItems', {}).get('ar', []):
    open_ar[r['KUNNR']] += r['HSL']
bps = []
for b in rows('BUT000'):
    p = b['PARTNER']
    m = KNA1.get(p) or LFA1.get(p) or {}
    bp = {'BusinessPartner': p, 'BusinessPartnerCategory': b['TYPE'], 'BusinessPartnerGrouping': b['BU_GROUP'],
          'OrganizationBPName1': b['NAME_ORG1'], 'BusinessPartnerFullName': b['NAME_ORG1'], 'SearchTerm1': b['BU_SORT1'],
          'Customer': p if p in KNA1 else '', 'Supplier': p if p in LFA1 else '',
          'to_BusinessPartnerRole': roles[p],
          'to_BusinessPartnerAddress': [{'BusinessPartner': p, 'AddressID': '1', 'CityName': m.get('ORT01', ''), 'Country': m.get('LAND1', '')}]}
    if p in KNA1:
        bp['to_Customer'] = {'Customer': p, 'CustomerName': KNA1[p]['NAME1'], 'to_CustomerCompany': knb1[p], 'to_CustomerSalesArea': knvv[p]}
    if p in LFA1:
        bp['to_Supplier'] = {'Supplier': p, 'SupplierName': LFA1[p]['NAME1'], 'to_SupplierCompany': lfb1[p], 'to_SupplierPurchasingOrg': lfm1[p]}
    # API에 없는 교육용 요약 (밑줄로 시작)
    bp['_stats'] = {'salesOrders': so_cnt.get(p, 0), 'salesAmountKRW': so_amt.get(p, 0), 'purchaseOrders': po_cnt.get(p, 0),
                    'purchaseAmountKRW': po_amt.get(p, 0), 'openReceivableKRW': open_ar.get(p, 0)}
    bps.append(bp)
write('apps/bp/webapp/model/businessPartners.json', {'A_BusinessPartner': bps, '_glNames': GL})

# ───────── 분개 조회: ACDOCA (빈 값은 생략해서 크기를 줄임) ─────────
KEEP = ['RLDNR', 'RBUKRS', 'GJAHR', 'BELNR', 'DOCLN', 'BLART', 'BUDAT', 'POPER', 'RACCT', 'DRCRK', 'HSL', 'RHCUR', 'WSL', 'RWCUR',
        'RCNTR', 'AUFNR', 'PRCTR', 'KUNNR', 'LIFNR', 'MATNR', 'WERKS', 'AWTYP', 'AWREF', 'SGTXT']
acd = [{k: r[k] for k in KEEP if r.get(k) not in ('', None)} for r in ACD]
blart = {'SA': 'G/L 계정 전표', 'WA': '출고', 'WE': '입고', 'WL': '출고 (출하)', 'RV': '청구 → 회계', 'DZ': '고객 입금', 'RE': '송장 (구매)',
         'KZ': '공급업체 지급', 'AF': '감가상각', 'CO': 'CO 내부 이동 (교육용 표시)', 'AA': '자산 전기'}
used = sorted({r['BLART'] for r in ACD})
cc = {r['KOSTL']: r['KTEXT'] for r in rows('CSKS')}
heads = {k: {'BKTXT': v.get('BKTXT', ''), 'XBLNR': v.get('XBLNR', ''), 'BLDAT': v.get('BLDAT', '')} for k, v in BKPF.items()}
write('apps/je/webapp/model/acdoca.json', {'ACDOCA': acd, 'GL': GL, 'BLART': {b: blart.get(b, '') for b in used}, 'CC': cc, 'BKPF': heads}, compact=True)


# ───────── 코드 이름 (설정 테이블 텍스트) ─────────
zterms = sorted({h['ZTERM'] for h in VBAK} | {r['ZTERM'] for r in rows('KNB1')} | {r['ZTERM'] for r in rows('LFB1')})
texts = {
    'vkorg': {r['VKORG']: r['VTEXT'] for r in rows('TVKO')},
    'vtweg': {r['VTWEG']: r['VTEXT'] for r in rows('TVTW')},
    'spart': {r['SPART']: r['VTEXT'] for r in rows('TSPA')},
    'plant': {r['WERKS']: r['NAME1'] for r in rows('T001W')},
    'ekorg': {r['EKORG']: r['EKOTX'] for r in rows('T024E')},
    'zterm': {z: f'청구 후 {int(z[2:])}일 이내 지급' for z in zterms if z[2:].isdigit()},
    'auart': {'OR': '표준 오더'},
    'pstyv': {'TAN': '일반 출하 품목'},
    'inco': {'DAP': '도착지 인도 (Delivered at Place)', 'FOB': '본선 인도 (Free on Board)'},
    'docCat': {'J': '출하문서', 'R': '재고 이동 (자재문서)', 'M': '청구문서'},
}
for app in ('so-json', 'so-odata', 'bp'):
    write(f'apps/{app}/webapp/model/texts.json', texts)

# ───────── 런치패드 타일 숫자 ─────────
write('launchpad/tiles.json', {'company': D['company']['name'], 'salesOrders': len(VBAK), 'businessPartners': len(bps),
                              'customers': len(KNA1), 'suppliers': len(LFA1), 'journalLines': len(ACD), 'journalEntries': len(BKPF),
                              'period': D['company']['period']})
