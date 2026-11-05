#!/usr/bin/env python3
"""
SAP 교육용 가상 회사 데이터 생성기  (schema: sap-edu-company/1)

- 회사 하나의 마스터 데이터와 3개월치 업무(판매·구매·생산·품질·회계·원가)를 하루 단위로 시뮬레이션해
  SAP 표준 테이블 이름/필드 이름을 쓴 JSON 하나로 내보냅니다.
- 다른 회사를 만들려면 CONFIG 블록만 바꾸고 다시 실행합니다. 같은 seed면 같은 결과가 나옵니다.
- 모든 숫자는 가상입니다. 테이블에는 학습에 필요한 열만 넣었습니다 (실제 테이블은 열이 훨씬 많음).

사용: python3 generate_company.py  →  gaon.json
"""
import json, math, random, datetime as dt
from collections import defaultdict

# ════════════════════════════════ CONFIG ════════════════════════════════
CONFIG = {
    'id': 'gaon', 'seed': 20261104,
    'name': '가온전자(주)', 'nameEn': 'Gaon Electronics Co., Ltd.', 'industry': '소형 가전 제조 (공기청정기·가습기·주방가전)',
    'start': '2026-08-03', 'end': '2026-10-30', 'opening': '2026-07-31',
    'bukrs': '1100', 'butxt': '가온전자(주)', 'waers': 'KRW', 'ktopl': 'GAON', 'kokrs': '1000', 'fx': {'USD': 1380},
    'vat': 0.10,
    'plants': {
        '1110': {'name': '평택공장', 'slocs': {'RM10': '원자재 창고', 'SF10': '반제품 창고', 'FG10': '완제품 창고'}, 'vstel': '1110', 'prctr': 'PC-AIR'},
        '1120': {'name': '구미공장', 'slocs': {'RM20': '원자재 창고', 'SF20': '반제품 창고', 'FG20': '완제품 창고'}, 'vstel': '1120', 'prctr': 'PC-KIT'},
    },
    'vkorgs': {'1100': '국내영업', '1200': '해외영업'},
    'vtwegs': {'10': '유통 (도매)', '20': '온라인'},
    'spart': {'10': '생활가전', '20': '주방가전'},
    'ekorg': {'1100': '가온전자 구매'},
    'ekgrp': {'P01': '전자부품', 'P02': '기구·포장', 'P03': '상품 (필터)'},
    'prctrs': {'PC-AIR': '공기·생활가전 사업', 'PC-KIT': '주방가전 사업', 'PC-CORP': '본사 공통'},
    'segment': 'SEG-HA',
    'kostl': {  # 원가센터: 이름, 범주, 손익센터, 월 급여, 월 전력비
        '4110': ('평택 조립', 'F', 'PC-AIR', 60_000_000, 9_800_000),
        '4120': ('구미 조립', 'F', 'PC-KIT', 42_000_000, 7_600_000),
        '4210': ('품질검사', 'F', 'PC-CORP', 24_000_000, 1_900_000),
        '4300': ('설비보전', 'F', 'PC-CORP', 15_000_000, 1_400_000),
        '5100': ('국내영업', 'V', 'PC-CORP', 48_000_000, 0),
        '5200': ('해외영업', 'V', 'PC-CORP', 24_000_000, 0),
        '6100': ('구매', 'W', 'PC-CORP', 18_000_000, 0),
        '7100': ('경영지원', 'W', 'PC-CORP', 36_000_000, 0),
        '7200': ('전산', 'W', 'PC-CORP', 14_000_000, 0),
    },
    'rent': ('7100', 18_000_000),
    'assess': {'7100': {'4110': 30, '4120': 25, '5100': 25, '5200': 10, '6100': 10}, '7200': {'4110': 20, '4120': 20, '5100': 25, '5200': 15, '7100': 20}, '4300': {'4110': 55, '4120': 45}},
    'acts': {'ASM': ('조립 시간', 'H'), 'QCT': ('검사 시간', 'H')},
    'wcs': {  # 작업장: 플랜트, 원가센터, 활동 유형, 단가(원/H)
        'A-ASM1': ('1110', '4110', 'ASM', 42_000, '조립라인 A1'), 'A-QC1': ('1110', '4210', 'QCT', 45_000, '검사대 A'),
        'B-ASM1': ('1120', '4120', 'ASM', 38_000, '조립라인 B1'), 'B-QC1': ('1120', '4210', 'QCT', 45_000, '검사대 B'),
    },
    'assets': [  # 번호, 클래스, 이름, 원가센터, 취득가, 월 감가상각
        ('10000001', '3000', '조립라인 A1 설비', '4110', 960_000_000, 8_000_000),
        ('10000002', '3000', '조립라인 B1 설비', '4120', 720_000_000, 6_000_000),
        ('10000003', '3000', '검사 장비 세트', '4210', 240_000_000, 2_000_000),
        ('10000004', '3000', '금형·지그', '4300', 180_000_000, 1_500_000),
        ('20000001', '5000', '업무용 PC·서버', '7200', 120_000_000, 2_500_000),
    ],
}

# 자재: 번호 → (내역, 유형, 자재그룹, 플랜트들, 조달 E/F, 표준가(ROH/HAWA), 판매가(FERT/HAWA), 안전재고, 반올림, 리드타임일, QM)
MATS = {
    'AP-100': ('공기청정기 소형 (20㎡)', 'FERT', 'HA-AIR', ['1110'], 'E', None, 129_000, 60, 50, 2, False),
    'AP-200': ('공기청정기 중형 (40㎡)', 'FERT', 'HA-AIR', ['1110'], 'E', None, 189_000, 50, 50, 2, False),
    'AP-300': ('공기청정기 대형 (60㎡)', 'FERT', 'HA-AIR', ['1110'], 'E', None, 269_000, 30, 30, 3, False),
    'HU-40': ('가습기 4L', 'FERT', 'HA-HUM', ['1110'], 'E', None, 79_000, 50, 50, 2, False),
    'HU-60': ('가습기 6L', 'FERT', 'HA-HUM', ['1110'], 'E', None, 99_000, 40, 50, 2, False),
    'KT-15': ('전기포트 1.5L', 'FERT', 'HA-KIT', ['1120'], 'E', None, 49_000, 80, 100, 2, False),
    'KT-17': ('전기포트 1.7L 온도조절', 'FERT', 'HA-KIT', ['1120'], 'E', None, 69_000, 60, 50, 2, False),
    'AF-35': ('에어프라이어 3.5L', 'FERT', 'HA-KIT', ['1120'], 'E', None, 89_000, 50, 50, 2, False),
    'AF-55': ('에어프라이어 5.5L', 'FERT', 'HA-KIT', ['1120'], 'E', None, 119_000, 40, 50, 3, False),
    'FT-100': ('교체필터 소형', 'HAWA', 'HA-FLT', ['1110'], 'F', 8_000, 15_900, 100, 100, 7, False),
    'FT-200': ('교체필터 중형', 'HAWA', 'HA-FLT', ['1110'], 'F', 11_000, 21_900, 100, 100, 7, False),
    'FT-300': ('교체필터 대형', 'HAWA', 'HA-FLT', ['1110'], 'F', 15_000, 28_900, 60, 100, 7, False),
    'SA-FAN': ('팬모터 어셈블리', 'HALB', 'SA', ['1110'], 'E', None, None, 60, 100, 1, False),
    'SA-ACT': ('공기 제어보드 어셈블리', 'HALB', 'SA', ['1110'], 'E', None, None, 60, 100, 1, False),
    'SA-HTR': ('포트 히터 어셈블리', 'HALB', 'SA', ['1120'], 'E', None, None, 60, 100, 1, False),
    'SA-KCT': ('주방 제어보드 어셈블리', 'HALB', 'SA', ['1120'], 'E', None, None, 60, 100, 1, False),
    'MOT-24': ('BLDC 모터 24V', 'ROH', 'EL-MOT', ['1110'], 'F', 18_000, None, 150, 200, 7, False),
    'FAN-180': ('팬 블레이드 180mm', 'ROH', 'ME-PLA', ['1110'], 'F', 2_400, None, 150, 200, 6, False),
    'PCB-AIR': ('공기 메인 PCB', 'ROH', 'EL-PCB', ['1110'], 'F', 9_500, None, 120, 200, 7, True),
    'SEN-PM': ('미세먼지 센서', 'ROH', 'EL-SEN', ['1110'], 'F', 6_800, None, 120, 200, 7, True),
    'PWR-24': ('전원 어댑터 24V', 'ROH', 'EL-PWR', ['1110'], 'F', 4_200, None, 150, 200, 7, False),
    'HSG-A1': ('하우징 소형', 'ROH', 'ME-PLA', ['1110'], 'F', 7_500, None, 60, 100, 8, False),
    'HSG-A2': ('하우징 중형', 'ROH', 'ME-PLA', ['1110'], 'F', 9_800, None, 50, 100, 8, False),
    'HSG-A3': ('하우징 대형', 'ROH', 'ME-PLA', ['1110'], 'F', 13_500, None, 30, 100, 8, False),
    'FLT-H13': ('HEPA H13 필터 (조립용)', 'ROH', 'ME-FLT', ['1110'], 'F', 5_500, None, 200, 300, 7, False),
    'TNK-40': ('물탱크 4L', 'ROH', 'ME-PLA', ['1110'], 'F', 3_900, None, 60, 100, 6, False),
    'TNK-60': ('물탱크 6L', 'ROH', 'ME-PLA', ['1110'], 'F', 4_800, None, 50, 100, 6, False),
    'ULT-01': ('초음파 진동자', 'ROH', 'EL-SEN', ['1110'], 'F', 5_200, None, 100, 200, 7, True),
    'CRD-KR': ('전원 코드 (KC)', 'ROH', 'EL-PWR', ['1110', '1120'], 'F', 1_300, None, 200, 500, 5, False),
    'BOX-S': ('포장박스 소', 'ROH', 'PK-BOX', ['1110', '1120'], 'F', 900, None, 200, 500, 4, False),
    'BOX-M': ('포장박스 중', 'ROH', 'PK-BOX', ['1110', '1120'], 'F', 1_200, None, 200, 500, 4, False),
    'BOX-L': ('포장박스 대', 'ROH', 'PK-BOX', ['1110', '1120'], 'F', 1_600, None, 100, 300, 4, False),
    'HTR-PL': ('히팅 플레이트', 'ROH', 'EL-HTR', ['1120'], 'F', 7_800, None, 120, 200, 8, False),
    'HTR-CO': ('열선 히터', 'ROH', 'EL-HTR', ['1120'], 'F', 9_600, None, 100, 200, 8, False),
    'PCB-KIT': ('주방 제어 PCB', 'ROH', 'EL-PCB', ['1120'], 'F', 6_900, None, 120, 200, 7, True),
    'SEN-TH': ('온도 센서', 'ROH', 'EL-SEN', ['1120'], 'F', 1_800, None, 200, 400, 6, False),
    'BDY-15': ('스테인리스 바디 1.5L', 'ROH', 'ME-MET', ['1120'], 'F', 8_200, None, 80, 100, 9, False),
    'BDY-17': ('스테인리스 바디 1.7L', 'ROH', 'ME-MET', ['1120'], 'F', 9_100, None, 60, 100, 9, False),
    'BSK-35': ('바스켓 3.5L', 'ROH', 'ME-MET', ['1120'], 'F', 5_600, None, 50, 100, 8, False),
    'BSK-55': ('바스켓 5.5L', 'ROH', 'ME-MET', ['1120'], 'F', 7_400, None, 40, 100, 8, False),
    'HSG-F35': ('프라이어 하우징 3.5L', 'ROH', 'ME-PLA', ['1120'], 'F', 8_800, None, 50, 100, 8, False),
    'HSG-F55': ('프라이어 하우징 5.5L', 'ROH', 'ME-PLA', ['1120'], 'F', 11_200, None, 40, 100, 8, False),
}
# BOM: 상위 → [(구성품, 수량)], 라우팅: 상위 → [(공정, 작업장, 표준시간/EA)]
BOM = {
    'SA-FAN': [('MOT-24', 1), ('FAN-180', 1)], 'SA-ACT': [('PCB-AIR', 1), ('SEN-PM', 1), ('PWR-24', 1)],
    'SA-HTR': [('HTR-PL', 1), ('SEN-TH', 1)], 'SA-KCT': [('PCB-KIT', 1), ('SEN-TH', 1)],
    'AP-100': [('SA-FAN', 1), ('SA-ACT', 1), ('HSG-A1', 1), ('FLT-H13', 1), ('CRD-KR', 1), ('BOX-S', 1)],
    'AP-200': [('SA-FAN', 1), ('SA-ACT', 1), ('HSG-A2', 1), ('FLT-H13', 2), ('CRD-KR', 1), ('BOX-M', 1)],
    'AP-300': [('SA-FAN', 2), ('SA-ACT', 1), ('HSG-A3', 1), ('FLT-H13', 3), ('CRD-KR', 1), ('BOX-L', 1)],
    'HU-40': [('TNK-40', 1), ('ULT-01', 1), ('SA-ACT', 1), ('CRD-KR', 1), ('BOX-S', 1)],
    'HU-60': [('TNK-60', 1), ('ULT-01', 1), ('SA-ACT', 1), ('CRD-KR', 1), ('BOX-M', 1)],
    'KT-15': [('SA-HTR', 1), ('BDY-15', 1), ('CRD-KR', 1), ('BOX-S', 1)],
    'KT-17': [('SA-HTR', 1), ('SA-KCT', 1), ('BDY-17', 1), ('CRD-KR', 1), ('BOX-M', 1)],
    'AF-35': [('HTR-CO', 1), ('SA-KCT', 1), ('BSK-35', 1), ('HSG-F35', 1), ('CRD-KR', 1), ('BOX-M', 1)],
    'AF-55': [('HTR-CO', 1), ('SA-KCT', 1), ('BSK-55', 1), ('HSG-F55', 1), ('CRD-KR', 1), ('BOX-L', 1)],
}
ROUT = {}
for m in ['SA-FAN', 'SA-ACT']: ROUT[m] = [('0010', 'A-ASM1', {'SA-FAN': .10, 'SA-ACT': .08}[m])]
for m in ['SA-HTR', 'SA-KCT']: ROUT[m] = [('0010', 'B-ASM1', {'SA-HTR': .06, 'SA-KCT': .07}[m])]
for m, a, q in [('AP-100', .35, .08), ('AP-200', .45, .10), ('AP-300', .60, .12), ('HU-40', .30, .06), ('HU-60', .35, .07)]:
    ROUT[m] = [('0010', 'A-ASM1', a), ('0020', 'A-QC1', q)]
for m, a, q in [('KT-15', .20, .05), ('KT-17', .25, .06), ('AF-35', .40, .08), ('AF-55', .50, .10)]:
    ROUT[m] = [('0010', 'B-ASM1', a), ('0020', 'B-QC1', q)]

# 고객: 번호, 이름, 국가, 도시, 판매조직, 유통경로, 제품군들, 지급조건, 통화, 비중, 고객그룹
CUSTS = [
    ('1000010', '누리가전마트', 'KR', '서울', '1100', '10', ['10', '20'], 'NT30', 'KRW', 9, '01'),
    ('1000011', '다솜전자유통', 'KR', '부산', '1100', '10', ['10', '20'], 'NT45', 'KRW', 7, '01'),
    ('1000012', '바름리빙', 'KR', '대구', '1100', '10', ['20'], 'NT30', 'KRW', 5, '01'),
    ('1000013', '새봄종합상사', 'KR', '광주', '1100', '10', ['10', '20'], 'NT60', 'KRW', 6, '01'),
    ('1000014', '가람홈플라자', 'KR', '대전', '1100', '10', ['10'], 'NT30', 'KRW', 5, '01'),
    ('1000015', '푸른가전', 'KR', '인천', '1100', '10', ['10', '20'], 'NT45', 'KRW', 6, '01'),
    ('1000016', '한울전자상가', 'KR', '수원', '1100', '10', ['10', '20'], 'NT30', 'KRW', 4, '01'),
    ('1000017', '이음생활마트', 'KR', '청주', '1100', '10', ['20'], 'NT30', 'KRW', 3, '01'),
    ('1000018', '모아리빙센터', 'KR', '창원', '1100', '10', ['10'], 'NT60', 'KRW', 3, '01'),
    ('1000019', '하늘상사', 'KR', '울산', '1100', '10', ['10', '20'], 'NT30', 'KRW', 3, '01'),
    ('1000020', '온새미몰', 'KR', '서울', '1100', '20', ['10', '20'], 'NT15', 'KRW', 8, '02'),
    ('1000021', '도담마켓', 'KR', '성남', '1100', '20', ['10', '20'], 'NT15', 'KRW', 6, '02'),
    ('1000022', '솔빛쇼핑', 'KR', '서울', '1100', '20', ['10', '20'], 'NT15', 'KRW', 5, '02'),
    ('1000023', '라온스토어', 'KR', '고양', '1100', '20', ['20'], 'NT15', 'KRW', 4, '02'),
    ('1000024', '나래홈쇼핑', 'KR', '서울', '1100', '20', ['10', '20'], 'NT30', 'KRW', 4, '02'),
    ('1000030', 'Brightwell Home Inc.', 'US', 'Seattle', '1200', '10', ['10', '20'], 'NT60', 'USD', 2, '03'),
    ('1000031', 'Kestrel Living Ltd.', 'GB', 'Leeds', '1200', '10', ['10'], 'NT60', 'USD', 2, '03'),
    ('1000032', 'Mariposa Hogar S.A.', 'MX', 'Monterrey', '1200', '10', ['20'], 'NT60', 'USD', 2, '03'),
    ('1000033', 'Saigon Bloom Trading', 'VN', 'Ho Chi Minh', '1200', '10', ['10', '20'], 'NT45', 'USD', 2, '03'),
]
# 공급업체: 번호, 이름, 도시, 지급조건, 공급 자재, 가격 배율
SUPS = [
    ('2000010', '한별모터', '화성', 'NT30', ['MOT-24'], 1.02),
    ('2000011', '누리피씨비', '구미', 'NT45', ['PCB-AIR', 'PCB-KIT'], 0.98),
    ('2000012', '맑은센서', '성남', 'NT30', ['SEN-PM', 'SEN-TH', 'ULT-01'], 1.03),
    ('2000013', '빛나전원', '안산', 'NT30', ['PWR-24', 'CRD-KR'], 0.99),
    ('2000014', '미래사출', '평택', 'NT60', ['FAN-180', 'HSG-A1', 'HSG-A2', 'HSG-A3', 'TNK-40', 'TNK-60'], 1.00),
    ('2000015', '청정필터', '오산', 'NT30', ['FLT-H13', 'FT-100', 'FT-200', 'FT-300'], 1.01),
    ('2000016', '동방포장', '천안', 'NT30', ['BOX-S', 'BOX-M', 'BOX-L'], 0.97),
    ('2000017', '단단금속', '김천', 'NT45', ['BDY-15', 'BDY-17', 'BSK-35', 'BSK-55'], 1.04),
    ('2000018', '열정히터', '칠곡', 'NT30', ['HTR-PL', 'HTR-CO'], 1.01),
    ('2000019', '구미사출', '구미', 'NT60', ['HSG-F35', 'HSG-F55'], 0.99),
]
GL = [  # 계정, 이름, 유형(X/P/S), 원가요소 범주, 조정계정 유형
    ('110100', '보통예금', 'X', '', ''), ('113100', '외상매출금', 'X', '', 'D'), ('114100', '부가세대급금', 'X', '', ''),
    ('121100', '원재료', 'X', '', ''), ('121500', '반제품', 'X', '', ''), ('122100', '제품', 'X', '', ''), ('123100', '상품', 'X', '', ''),
    ('151100', '기계장치', 'X', '', ''), ('151900', '감가상각누계액-기계장치', 'X', '', ''), ('152100', '비품', 'X', '', ''), ('152900', '감가상각누계액-비품', 'X', '', ''),
    ('211100', '외상매입금', 'X', '', 'K'), ('211900', 'GR/IR 정산', 'X', '', ''), ('213100', '부가세예수금', 'X', '', ''), ('253000', '미지급급여', 'X', '', ''),
    ('310000', '자본금', 'X', '', ''), ('399900', '기초재고 이관', 'X', '', ''),
    ('410000', '제품매출', 'P', '11', ''), ('411000', '상품매출', 'P', '11', ''),
    ('510000', '제품매출원가', 'P', '01', ''), ('511000', '상품매출원가', 'P', '01', ''),
    ('520100', '원재료비 (생산 투입)', 'P', '01', ''), ('520900', '생산 입고 대체', 'P', '01', ''), ('520950', '생산오더 정산', 'P', '01', ''),
    ('531000', '생산 차이', 'P', '01', ''), ('532000', '구매 가격차이', 'P', '01', ''),
    ('610000', '급여', 'P', '01', ''), ('620000', '감가상각비', 'P', '01', ''), ('630000', '전력·수도비', 'P', '01', ''), ('640000', '임차료', 'P', '01', ''),
    ('942000', '관리비 배부', 'S', '42', ''), ('943100', '조립 작업', 'S', '43', ''), ('943200', '검사 작업', 'S', '43', ''),
]
INV_ACCT = {'ROH': '121100', 'HALB': '121500', 'FERT': '122100', 'HAWA': '123100'}
BKLAS = {'ROH': '3000', 'HALB': '7900', 'FERT': '7920', 'HAWA': '3100'}

# ════════════════════════════════ 준비 ════════════════════════════════
C = CONFIG
R = random.Random(C['seed'])
RL = random.Random(C['seed'] + 7)  # 입금 지연 전용 (다른 데이터의 난수 순서를 바꾸지 않도록 분리)
SLOW_PAYERS = {'1000013', '1000018', '1000021', '1000033'}  # 자주 늦게 입금하는 고객
D = lambda s: dt.date.fromisoformat(s)
START, END, OPEN = D(C['start']), D(C['end']), D(C['opening'])
DAYS = [START + dt.timedelta(i) for i in range((END - START).days + 1)]
BDAYS = [d for d in DAYS if d.weekday() < 5]
iso = lambda d: d.isoformat()
def addb(d, n):  # 영업일 더하기
    x = d
    while n > 0:
        x += dt.timedelta(1)
        if x.weekday() < 5: n -= 1
    return x
def next_bday(d):
    x = d
    while x.weekday() >= 5: x += dt.timedelta(1)
    return x
FX = C['fx']['USD']
VAT = C['vat']

SALES_FACTOR = 0.92
for _m, _t in list(MATS.items()):
    if _t[6]: MATS[_m] = _t[:6] + (int(round(_t[6] * SALES_FACTOR, -2)),) + _t[7:]
# 표준원가 계산 (구성품 + 활동)
WC = C['wcs']
STD = {}
def std(m):
    if m in STD: return STD[m]
    t = MATS[m]
    if t[4] == 'F': STD[m] = t[5]
    else:
        v = sum(std(c) * q for c, q in BOM[m]) + sum(h * WC[w][3] for _, w, h in ROUT[m])
        STD[m] = int(round(v, -1))
    return STD[m]
for m in MATS: std(m)
LLC = {}
def llc(m):
    if m in LLC: return LLC[m]
    parents = [p for p, comps in BOM.items() if any(c == m for c, _ in comps)]
    LLC[m] = 0 if not parents else 1 + max(llc(p) for p in parents)
    return LLC[m]
for m in MATS: llc(m)
PLANT_OF = lambda m: MATS[m][3][0]
SLOC = lambda m, w: {'ROH': 'RM', 'HAWA': 'FG', 'HALB': 'SF', 'FERT': 'FG'}[MATS[m][1]] + w[2] + '0'
PRCTR = lambda m, w: C['plants'][w]['prctr']
SUP_OF = {}
for s in SUPS:
    for m in s[4]: SUP_OF[m] = s
INFO_PRICE = {m: int(round(MATS[m][5] * SUP_OF[m][5] * R.uniform(0.985, 1.03), -1)) for m in SUP_OF}

# ── 문서 번호
class Num:
    def __init__(self, start): self.n = start
    def __call__(self):
        self.n += 1; return str(self.n)
N = {k: Num(v) for k, v in {
    'VBAK': 10000000, 'LIKP': 80000000, 'VBRK': 90000000, 'BANF': 10000000, 'EBELN': 4500000000, 'MBLNR': 4900000000,
    'RBKP': 5105600000, 'PLAF': 100000, 'AUFNR': 1000000, 'RSNUM': 100000, 'RUECK': 10000, 'QALS': 10000000000, 'COBK': 100000000,
    'WE': 5000000000, 'RE': 5100000000, 'RV': 9400000000, 'DZ': 1400000000, 'KZ': 1500000000, 'SA': 100000000, 'AF': 200000000, 'CO': 300000000,
}.items()}
FI_RANGE = {'WE': 'WE', 'WA': 'WE', 'WL': 'WE', 'WI': 'WE', 'RE': 'RE', 'RV': 'RV', 'DZ': 'DZ', 'KZ': 'KZ', 'SA': 'SA', 'AF': 'AF', 'CO': 'CO'}

T = defaultdict(list)          # 테이블 → 행(dict)
FLOW = []                      # (from_type, from_no, to_type, to_no)
EV = defaultdict(lambda: defaultdict(int))   # 노선도 역 → 날짜 → 건수
def ev(st, d, n=1): EV[st][iso(d)] += n

# ── 회계 전표
def post(blart, d, lines, awtyp, awref, bktxt='', xblnr='', waers='KRW'):
    assert lines, 'empty'
    s = sum(l['hsl'] for l in lines)
    assert abs(s) < 1e-6, (blart, awref, s, lines)
    belnr = N[FI_RANGE[blart]]()
    if blart != 'CO':
        T['BKPF'].append(dict(BUKRS=C['bukrs'], BELNR=belnr, GJAHR=d.year, BLART=blart, BLDAT=iso(d), BUDAT=iso(d), XBLNR=xblnr, AWTYP=awtyp, AWKEY=awref, WAERS=waers, BKTXT=bktxt))
    for i, l in enumerate(lines):
        racct = l['racct']; gtype = GLT[racct]
        T['ACDOCA'].append(dict(
            RLDNR='0L', RBUKRS=C['bukrs'], GJAHR=d.year, BELNR=belnr, DOCLN=f'{i + 1:06d}', BLART=blart, BUDAT=iso(d), POPER=f'{d.month:03d}',
            RACCT=racct, DRCRK='S' if l['hsl'] >= 0 else 'H', HSL=l['hsl'], RHCUR='KRW', WSL=l.get('wsl', l['hsl']), RWCUR=l.get('rwcur', 'KRW'),
            KTOSL=l.get('ktosl', ''), RCNTR=l.get('rcntr', ''), AUFNR=l.get('aufnr', ''), PRCTR=l.get('prctr', ''), SEGMENT=C['segment'] if l.get('prctr') else '',
            KUNNR=l.get('kunnr', ''), LIFNR=l.get('lifnr', ''), MATNR=l.get('matnr', ''), WERKS=l.get('werks', ''), MSL=l.get('msl', 0), RUNIT=l.get('runit', ''),
            ANLN1=l.get('anln1', ''), KOKRS=C['kokrs'] if gtype in ('P', 'S') else '', AWTYP=awtyp, AWREF=awref, SGTXT=l.get('sgtxt', '')))
    return belnr
GLT = {g[0]: g[2] for g in GL}
CC_PC = {k: v[2] for k, v in C['kostl'].items()}

# ── 재고 (U 사용가능, Q 품질검사)
STOCK = defaultdict(float)
def stock(m, w, typ='U'): return STOCK[(m, w, typ)]
def matdoc(d, bwart, items, xblnr='', hdr_txt=''):
    mblnr = N['MBLNR']()
    for i, it in enumerate(items):
        m, w, q = it['matnr'], it['werks'], it['menge']
        lg = it.get('lgort', SLOC(m, w))
        shkzg = 'S' if bwart in ('101', '561', '321') else 'H'
        if bwart == '321':  # 품질검사 → 사용가능 (같은 수량 두 줄)
            pass
        typ = it.get('insmk', 'U')
        if shkzg == 'S':
            STOCK[(m, w, typ)] += q
            if bwart == '321': STOCK[(m, w, 'Q')] -= q
        else:
            STOCK[(m, w, typ)] -= q
            assert STOCK[(m, w, typ)] >= -1e-6, ('neg stock', m, w, bwart, d, STOCK[(m, w, typ)])
        T['MATDOC'].append(dict(MBLNR=mblnr, MJAHR=d.year, ZEILE=f'{i + 1:04d}', BWART=bwart, MATNR=m, WERKS=w, LGORT=lg, MENGE=q, MEINS='EA',
                                SHKZG=shkzg, DMBTR=it.get('dmbtr', 0), BUDAT=iso(d), BLDAT=iso(d), XBLNR=xblnr, INSMK='X' if typ == 'Q' else '',
                                EBELN=it.get('ebeln', ''), EBELP=it.get('ebelp', ''), AUFNR=it.get('aufnr', ''), VBELN_IM=it.get('vbeln', ''), VBELP_IM=it.get('posnr', ''),
                                KUNNR=it.get('kunnr', ''), LIFNR=it.get('lifnr', ''), RSNUM=it.get('rsnum', ''), RSPOS=it.get('rspos', '')))
    return mblnr

# ════════════════════════════════ 마스터 데이터 ════════════════════════════════
T['T001'].append(dict(BUKRS=C['bukrs'], BUTXT=C['butxt'], LAND1='KR', WAERS='KRW', KTOPL=C['ktopl']))
T['TKA01'].append(dict(KOKRS=C['kokrs'], BEZEI=C['name'] + ' 관리회계 영역', WAERS='KRW', KTOPL=C['ktopl']))
for w, p in C['plants'].items():
    T['T001W'].append(dict(WERKS=w, NAME1=p['name'], BWKEY=w, BUKRS=C['bukrs']))
    for lg, n in p['slocs'].items(): T['T001L'].append(dict(WERKS=w, LGORT=lg, LGOBE=n))
    T['TVST'].append(dict(VSTEL=p['vstel'], WERKS=w, VTEXT=p['name'] + ' 출하장'))
for k, n in C['vkorgs'].items(): T['TVKO'].append(dict(VKORG=k, VTEXT=n, BUKRS=C['bukrs'], WAERS='KRW'))
for k, n in C['vtwegs'].items(): T['TVTW'].append(dict(VTWEG=k, VTEXT=n))
for k, n in C['spart'].items(): T['TSPA'].append(dict(SPART=k, VTEXT=n))
for k, n in C['ekorg'].items(): T['T024E'].append(dict(EKORG=k, EKOTX=n, BUKRS=C['bukrs']))
for k, n in C['ekgrp'].items(): T['T024'].append(dict(EKGRP=k, EKNAM=n))
for g in GL:
    T['SKA1'].append(dict(KTOPL=C['ktopl'], SAKNR=g[0], TXT50=g[1], GLACCOUNT_TYPE=g[2], XBILK='X' if g[2] == 'X' else ''))
    T['SKB1'].append(dict(BUKRS=C['bukrs'], SAKNR=g[0], WAERS='KRW', MITKZ=g[4]))
    if g[3]: T['CSKB'].append(dict(KOKRS=C['kokrs'], KSTAR=g[0], DATBI='9999-12-31', KATYP=g[3]))
for k, v in C['prctrs'].items(): T['CEPC'].append(dict(PRCTR=k, KOKRS=C['kokrs'], DATBI='9999-12-31', KTEXT=v, SEGMENT=C['segment']))
for k, v in C['kostl'].items(): T['CSKS'].append(dict(KOKRS=C['kokrs'], KOSTL=k, DATBI='9999-12-31', DATAB='2026-01-01', KTEXT=v[0], KOSAR=v[1], PRCTR=v[2], BUKRS=C['bukrs']))
for k, v in C['acts'].items(): T['CSLA'].append(dict(KOKRS=C['kokrs'], LSTAR=k, DATBI='9999-12-31', KTEXT=v[0], LEINH=v[1]))
for i, (k, v) in enumerate(WC.items()):
    oid = f'{10000001 + i}'
    T['CRHD'].append(dict(OBJID=oid, ARBPL=k, WERKS=v[0], KTEXT=v[4]))
    T['CRCO'].append(dict(OBJID=oid, KOKRS=C['kokrs'], KOSTL=v[1], LSTAR=v[2], TARIF=v[3]))
WC_OBJ = {r['ARBPL']: r['OBJID'] for r in T['CRHD']}
for m, t in MATS.items():
    T['MARA'].append(dict(MATNR=m, MTART=t[1], MATKL=t[2], MEINS='EA', ERSDA='2025-11-01'))
    T['MAKT'].append(dict(MATNR=m, SPRAS='3', MAKTX=t[0]))
    for w in t[3]:
        T['MARC'].append(dict(MATNR=m, WERKS=w, BESKZ=t[4], DISMM='PD', DISPO='M01' if w == '1110' else 'M02', PLIFZ=t[9] if t[4] == 'F' else 0,
                              DZEIT=t[9] if t[4] == 'E' else 0, EISBE=t[7], BSTRF=t[8], QMATV='X' if t[10] else ''))
        T['MBEW'].append(dict(MATNR=m, BWKEY=w, BKLAS=BKLAS[t[1]], VPRSV='S', STPRS=STD[m], PEINH=1))
    if t[6]:
        for vk in (['1100', '1200']):
            for vt in (['10', '20'] if vk == '1100' else ['10']):
                T['MVKE'].append(dict(MATNR=m, VKORG=vk, VTWEG=vt, DWERK=t[3][0], MTPOS='NORM'))
        T['KONP'].append(dict(KSCHL='PPR0', MATNR=m, KBETR=t[6], KONWA='KRW', KPEIN=1, KMEIN='EA'))
for p, comps in BOM.items():
    stlnr = f'{len(T["MAST"]) + 1:08d}'
    T['MAST'].append(dict(MATNR=p, WERKS=PLANT_OF(p), STLAN='1', STLNR=stlnr))
    for i, (c, q) in enumerate(comps): T['STPO'].append(dict(STLNR=stlnr, POSNR=f'{(i + 1) * 10:04d}', IDNRK=c, MENGE=q, MEINS='EA'))
    plnnr = f'{len(T["PLKO"]) + 1:08d}'
    T['PLKO'].append(dict(PLNTY='N', PLNNR=plnnr, MATNR=p, WERKS=PLANT_OF(p), KTEXT=MATS[p][0] + ' 라우팅'))
    for vornr, wcn, h in ROUT[p]:
        T['PLPO'].append(dict(PLNNR=plnnr, VORNR=vornr, ARBID=WC_OBJ[wcn], LTXA1='조립' if 'ASM' in wcn else '검사', STEUS='PP01', VGW01=h, VGE01='H', LAR01=WC[wcn][2]))
for c in CUSTS:
    T['BUT000'].append(dict(PARTNER=c[0], TYPE='2', BU_GROUP='CUST', NAME_ORG1=c[1], BU_SORT1=c[1][:10].upper()))
    for r in ('FLCU00', 'FLCU01'): T['BUT100'].append(dict(PARTNER=c[0], RLTYP=r))
    T['KNA1'].append(dict(KUNNR=c[0], NAME1=c[1], LAND1=c[2], ORT01=c[3]))
    T['KNB1'].append(dict(KUNNR=c[0], BUKRS=C['bukrs'], AKONT='113100', ZTERM=c[7]))
    for sp in c[6]: T['KNVV'].append(dict(KUNNR=c[0], VKORG=c[4], VTWEG=c[5], SPART=sp, WAERS=c[8], ZTERM=c[7], KDGRP=c[10], INCO1='FOB' if c[8] == 'USD' else 'DAP'))
for s in SUPS:
    T['BUT000'].append(dict(PARTNER=s[0], TYPE='2', BU_GROUP='SUPL', NAME_ORG1=s[1], BU_SORT1=s[1][:10].upper()))
    for r in ('FLVN00', 'FLVN01'): T['BUT100'].append(dict(PARTNER=s[0], RLTYP=r))
    T['LFA1'].append(dict(LIFNR=s[0], NAME1=s[1], LAND1='KR', ORT01=s[2]))
    T['LFB1'].append(dict(LIFNR=s[0], BUKRS=C['bukrs'], AKONT='211100', ZTERM=s[3]))
    T['LFM1'].append(dict(LIFNR=s[0], EKORG='1100', WAERS='KRW', ZTERM=s[3]))
    for m in s[4]:
        T['EINA'].append(dict(INFNR=f'53{len(T["EINA"]) + 1:08d}', MATNR=m, LIFNR=s[0]))
        T['EINE'].append(dict(INFNR=T['EINA'][-1]['INFNR'], EKORG='1100', WERKS=MATS[m][3][0], NETPR=INFO_PRICE[m], PEINH=1, APLFZ=MATS[m][9]))
for a in C['assets']:
    T['ANLA'].append(dict(BUKRS=C['bukrs'], ANLN1=a[0], ANLN2='0', ANLKL=a[1], TXT50=a[2], AKTIV='2024-01-02'))
    T['ANLZ'].append(dict(BUKRS=C['bukrs'], ANLN1=a[0], ANLN2='0', KOSTL=a[3], BDATU='9999-12-31'))

# ════════════════════════════════ 기초 잔액 ════════════════════════════════
mach = sum(a[4] for a in C['assets'] if a[1] == '3000'); it_ = sum(a[4] for a in C['assets'] if a[1] == '5000')
acc_m = sum(a[5] * 20 for a in C['assets'] if a[1] == '3000'); acc_i = sum(a[5] * 20 for a in C['assets'] if a[1] == '5000')
cash = 2_600_000_000
post('SA', OPEN, [dict(racct='110100', hsl=cash), dict(racct='151100', hsl=mach), dict(racct='152100', hsl=it_),
                  dict(racct='151900', hsl=-acc_m), dict(racct='152900', hsl=-acc_i), dict(racct='310000', hsl=-(cash + mach + it_ - acc_m - acc_i))],
     'BKPF', 'OPEN', '기초 잔액 이관')
init_items = []
for m, t in MATS.items():
    for w in t[3]:
        base = {'ROH': 9.0, 'HALB': 5.0, 'FERT': 8.0, 'HAWA': 6.0}[t[1]]
        q = int(math.ceil(t[7] * base * R.uniform(0.9, 1.3) / 10) * 10)
        init_items.append(dict(matnr=m, werks=w, menge=q, dmbtr=q * STD[m]))
mb = matdoc(OPEN, '561', init_items, hdr_txt='기초 재고')
lines = []
for it in init_items:
    lines += [dict(racct=INV_ACCT[MATS[it['matnr']][1]], hsl=it['dmbtr'], ktosl='BSX', matnr=it['matnr'], werks=it['werks'], msl=it['menge'], runit='EA', prctr=PRCTR(it['matnr'], it['werks'])),
              dict(racct='399900', hsl=-it['dmbtr'], ktosl='GBB', matnr=it['matnr'], werks=it['werks'], prctr=PRCTR(it['matnr'], it['werks']))]
post('WI', OPEN, lines, 'MKPF', mb + '2026', '기초 재고 이관 (이동유형 561)')

# ════════════════════════════════ 업무 객체 ════════════════════════════════
SO = {}      # vbeln → dict(head, items[ {posnr, matnr, qty, open, price...} ])
PO = {}      # ebeln → dict
PROD = {}    # aufnr → dict
OPEN_AR = []  # [ (vbrk, kunnr, due, gross_krw, gross_wsl, cur) ]
OPEN_AP = []  # [ (rbkp_belnr, lifnr, due, gross) ]
PEND_GR = []  # [(due_date, ebeln, ebelp)]
QI_LOTS = []  # [(ud_date, prueflos, matnr, werks, qty, mblnr)]
PRS_TO_CONVERT = []

def price_for(m, kunnr):
    c = CUST[kunnr]; p = MATS[m][6]
    if c[5] == '20': p = int(round(p * 0.97, -2))
    if c[8] == 'USD': return round(p * 0.92 / FX, 2)
    return p
CUST = {c[0]: c for c in CUSTS}
SUPP = {s[0]: s for s in SUPS}
DUE = lambda d, zterm: d + dt.timedelta(int(zterm[2:]))

def create_so(d):
    weights = [c[9] for c in CUSTS]
    c = R.choices(CUSTS, weights)[0]
    sp = R.choice(c[6])
    pool = [m for m, t in MATS.items() if t[6] and ((sp == '10' and t[2] in ('HA-AIR', 'HA-HUM', 'HA-FLT')) or (sp == '20' and t[2] == 'HA-KIT'))]
    if c[5] == '20': pool = [m for m in pool]
    n = R.choices([1, 2, 3], [5, 3, 2])[0]
    mats = R.sample(pool, min(n, len(pool)))
    vbeln = N['VBAK'](); cur = c[8]
    items = []; net = 0
    for i, m in enumerate(mats):
        if c[8] == 'USD': q = R.choice([100, 150, 200, 250])
        elif c[5] == '20': q = R.choice([20, 30, 40, 60, 80])
        else: q = R.choice([30, 40, 50, 60, 80, 100, 120, 150])
        if MATS[m][1] == 'HAWA': q *= 2
        pr = price_for(m, c[0]); amt = round(q * pr, 2) if cur == 'USD' else q * pr
        items.append(dict(posnr=f'{(i + 1) * 10:06d}', matnr=m, qty=q, open=q, price=pr, net=amt, werks=MATS[m][3][0]))
        net += amt
    vdatu = addb(d, R.randint(4, 14))
    head = dict(VBELN=vbeln, AUART='OR', VKORG=c[4], VTWEG=c[5], SPART=sp, KUNNR=c[0], ERDAT=iso(d), AUDAT=iso(d),
                BSTNK=f'{c[1][:2]}-PO-{R.randint(1000, 9999)}' if cur == 'KRW' else f'PO{R.randint(40000, 49999)}', VDATU=iso(vdatu),
                NETWR=round(net, 2), WAERK=cur, GBSTK='A', LFSTK='A', ZTERM=c[7], INCO1='FOB' if cur == 'USD' else 'DAP')
    SO[vbeln] = dict(head=head, items=items, vdatu=vdatu, cust=c)
    for it in items:
        T['VBAP'].append(dict(VBELN=vbeln, POSNR=it['posnr'], MATNR=it['matnr'], ARKTX=MATS[it['matnr']][0], KWMENG=it['qty'], VRKME='EA',
                              NETPR=it['price'], NETWR=it['net'], WAERK=cur, WERKS=it['werks'], PSTYV='TAN', GBSTA='A'))
    T['VBAK'].append(head)
    ev('so', d)

def deliver(d):
    committed = defaultdict(float)   # 먼저 들어온 주문이 기다리는 재고는 뒤 주문이 못 가져감 (FIFO)
    for vbeln, so in SO.items():
        if so['head']['GBSTK'] == 'C': continue
        if so['vdatu'] > addb(d, 2) and R.random() > 0.15: continue
        ready = []
        for it in so['items']:
            if it['open'] <= 0: continue
            k = (it['matnr'], it['werks'])
            if stock(*k) - committed[k] >= it['open']: ready.append(it)
            else: committed[k] += it['open']
        if not ready: continue
        by_plant = defaultdict(list)
        for it in ready: by_plant[it['werks']].append(it)
        for w, its in by_plant.items():
            lk = N['LIKP'](); c = so['cust']
            T['LIKP'].append(dict(VBELN=lk, LFART='LF', VSTEL=C['plants'][w]['vstel'], KUNNR=c[0], ERDAT=iso(d), WADAT=iso(d), WADAT_IST=iso(d), WBSTK='C', FKSTK='A'))
            mitems = []
            for j, it in enumerate(its):
                posnr = f'{(j + 1) * 10:06d}'
                T['LIPS'].append(dict(VBELN=lk, POSNR=posnr, MATNR=it['matnr'], LFIMG=it['open'], VRKME='EA', WERKS=w, LGORT=SLOC(it['matnr'], w), VGBEL=vbeln, VGPOS=it['posnr']))
                FLOW.append(('VBAK', vbeln, 'LIKP', lk))
                mitems.append(dict(matnr=it['matnr'], werks=w, menge=it['open'], dmbtr=it['open'] * STD[it['matnr']], vbeln=lk, posnr=posnr, kunnr=c[0]))
                it['dlv'] = it.get('dlv', []) + [(lk, posnr, it['open'])]
                it['open'] = 0
            mb = matdoc(d, '601', mitems)
            FLOW.append(('LIKP', lk, 'MATDOC', mb))
            lines = []
            for mi in mitems:
                cogs = '511000' if MATS[mi['matnr']][1] == 'HAWA' else '510000'
                pc = PRCTR(mi['matnr'], w)
                lines += [dict(racct=cogs, hsl=mi['dmbtr'], ktosl='GBB', matnr=mi['matnr'], werks=w, kunnr=c[0], prctr=pc, msl=mi['menge'], runit='EA', sgtxt='매출원가'),
                          dict(racct=INV_ACCT[MATS[mi['matnr']][1]], hsl=-mi['dmbtr'], ktosl='BSX', matnr=mi['matnr'], werks=w, prctr=pc, msl=-mi['menge'], runit='EA')]
            fi = post('WL', d, lines, 'MKPF', mb + str(d.year), '출고 ' + lk, lk)
            FLOW.append(('MATDOC', mb, 'BKPF', fi))
            PEND_BILL.append((addb(d, 1), lk, vbeln, w))
            ev('dlv', d); ev('pgi', d)
        for it in so['items']:
            pass
        st = 'C' if all(it['open'] == 0 for it in so['items']) else 'B'
        so['head']['LFSTK'] = st; so['head']['GBSTK'] = 'B'
PEND_BILL = []

def bill(d):
    global PEND_BILL
    keep = []
    for due, lk, vbeln, w in PEND_BILL:
        if due > d: keep.append((due, lk, vbeln, w)); continue
        so = SO[vbeln]; c = so['cust']; cur = so['head']['WAERK']
        vb = N['VBRK'](); net = 0; lines = []; rows = []
        dl = [r for r in T['LIPS'] if r['VBELN'] == lk]
        for j, r in enumerate(dl):
            it = next(i for i in so['items'] if i['posnr'] == r['VGPOS'])
            amt = round(r['LFIMG'] * it['price'], 2) if cur == 'USD' else r['LFIMG'] * it['price']
            net += amt
            hsl = int(round(amt * FX)) if cur == 'USD' else amt
            rev = '411000' if MATS[r['MATNR']][1] == 'HAWA' else '410000'
            rows.append(dict(VBELN=vb, POSNR=f'{(j + 1) * 10:06d}', MATNR=r['MATNR'], FKIMG=r['LFIMG'], VRKME='EA', NETWR=amt, VGBEL=lk, VGPOS=r['POSNR'], AUBEL=vbeln, AUPOS=it['posnr'], WERKS=w))
            lines.append(dict(racct=rev, hsl=-hsl, wsl=-amt, rwcur=cur, ktosl='ERL', matnr=r['MATNR'], werks=w, kunnr=c[0], prctr=PRCTR(r['MATNR'], w), msl=-r['LFIMG'], runit='EA', sgtxt='매출'))
            it['billed'] = it.get('billed', 0) + r['LFIMG']
        tax = 0 if cur == 'USD' else int(round(net * VAT))
        gross = net + tax
        ghsl = int(round(gross * FX)) if cur == 'USD' else gross
        ghsl = -sum(l['hsl'] for l in lines) + (tax if cur == 'KRW' else 0)
        if tax: lines.append(dict(racct='213100', hsl=-tax, ktosl='MWS', sgtxt='부가세'))
        lines.insert(0, dict(racct='113100', hsl=ghsl, wsl=gross, rwcur=cur, kunnr=c[0], sgtxt='고객 채권'))
        fi = post('RV', d, lines, 'VBRK', vb, '청구 ' + vb, vb, cur)
        T['VBRK'].append(dict(VBELN=vb, FKART='F2', FKDAT=iso(d), VKORG=so['head']['VKORG'], KUNAG=c[0], KUNRG=c[0], NETWR=net, MWSBK=tax, WAERK=cur, BELNR=fi, RFBSK='C', ZTERM=c[7]))
        T['VBRP'].extend(rows)
        for r in T['LIKP']:
            if r['VBELN'] == lk: r['FKSTK'] = 'C'
        FLOW.append(('LIKP', lk, 'VBRK', vb)); FLOW.append(('VBRK', vb, 'BKPF', fi))
        due_c = DUE(d, c[7])  # 지급조건상 만기일
        due_d = due_c + dt.timedelta(R.choice([-2, 0, 0, 0, 1, 3, 5, 9]))  # 실제 입금일
        if c[0] in SLOW_PAYERS: due_d += dt.timedelta(RL.choice([8, 14, 21, 30, 45]))
        OPEN_AR.append(dict(vbrk=vb, fi=fi, kunnr=c[0], due=due_d, duec=due_c, hsl=ghsl, wsl=gross, cur=cur, vbeln=vbeln))
        if all(it.get('billed', 0) >= it['qty'] for it in so['items']):
            so['head']['GBSTK'] = 'C'
        ev('bil', d)
    PEND_BILL = keep

def receive_payments(d):
    rest = []
    for ar in OPEN_AR:
        if ar['due'] <= d:
            fi = post('DZ', d, [dict(racct='110100', hsl=ar['hsl'], wsl=ar['wsl'], rwcur=ar['cur'], sgtxt='고객 입금'),
                                dict(racct='113100', hsl=-ar['hsl'], wsl=-ar['wsl'], rwcur=ar['cur'], kunnr=ar['kunnr'], sgtxt='채권 반제')],
                      'BKPF', 'DZ', '입금 ' + ar['vbrk'], ar['vbrk'], ar['cur'])
            T['BSE_CLR'].append(dict(BUKRS=C['bukrs'], BELNR=ar['fi'], AUGBL=fi, AUGDT=iso(d), KUNNR=ar['kunnr'], LIFNR=''))
            FLOW.append(('BKPF', ar['fi'], 'BKPF', fi))
            ev('payin', d)
        else: rest.append(ar)
    OPEN_AR[:] = rest

# ── MRP
def open_supply(m, w):
    q = stock(m, w, 'U') + stock(m, w, 'Q')
    q += sum(p['qty'] - p['gr'] for p in PROD.values() if p['matnr'] == m and p['werks'] == w and p['gr'] < p['qty'])
    q += sum(it['qty'] - it['gr'] for po in PO.values() for it in po['items'] if it['matnr'] == m and it['werks'] == w and it['gr'] < it['qty'])
    q += sum(pr['qty'] for pr in PRS_TO_CONVERT if pr['matnr'] == m and pr['werks'] == w)
    return q
def demand(m, w, d):
    t = MATS[m]
    q = 0
    if t[6]:
        horizon = addb(d, 12)
        q += sum(it['open'] for so in SO.values() for it in so['items'] if it['matnr'] == m and it['werks'] == w and so['vdatu'] <= horizon)
    q += sum(r['open'] for p in PROD.values() for r in p['resb'] if r['matnr'] == m and r['werks'] == w)
    if t[6]:  # 판매 자재: 최근 20영업일 평균 주문량으로 앞으로 8영업일 예측 수요 (계획 독립 소요)
        since = d - dt.timedelta(28)
        recent = sum(it['qty'] for so in SO.values() for it in so['items'] if it['matnr'] == m and it['werks'] == w and dt.date.fromisoformat(so['head']['ERDAT']) >= since)
        q = max(q, int(recent / 20 * 12))
    return q + t[7] * (4 if t[1] == 'ROH' else 2)
def run_mrp(d):
    created = 0
    for lvl in range(0, max(LLC.values()) + 1):
        for m in [x for x in MATS if LLC[x] == lvl]:
            for w in MATS[m][3]:
                net = demand(m, w, d) - open_supply(m, w)
                if net <= 0: continue
                rnd = MATS[m][8]
                q = int(math.ceil(net / rnd) * rnd)
                if MATS[m][4] == 'E':
                    plnum = N['PLAF']()
                    start = addb(d, 1); fin = addb(start, max(1, MATS[m][9]))
                    T['PLAF'].append(dict(PLNUM=plnum, MATNR=m, PLWRK=w, GSMNG=q, PSTTR=iso(start), PEDTR=iso(fin), PAART='LA', BESKZ='E', STATUS='생산오더로 전환'))
                    a = create_prod(d, m, w, q, start, fin, plnum)
                    FLOW.append(('PLAF', plnum, 'AUFK', a))
                else:
                    banfn = N['BANF']()
                    need = addb(d, MATS[m][9] + 1)
                    T['EBAN'].append(dict(BANFN=banfn, BNFPO='00010', BSART='NB', MATNR=m, TXZ01=MATS[m][0], MENGE=q, MEINS='EA', WERKS=w, LGORT=SLOC(m, w),
                                          LFDAT=iso(need), EKGRP='P03' if MATS[m][1] == 'HAWA' else ('P01' if MATS[m][2].startswith('EL') else 'P02'),
                                          BADAT=iso(d), ESTKZ='B', EBELN='', EBELP=''))
                    PRS_TO_CONVERT.append(dict(banfn=banfn, matnr=m, werks=w, qty=q, need=need, d=d))
                    ev('pr', d)
                created += 1
    ev('mrp', d, max(1, created))

def create_prod(d, m, w, q, start, fin, plnum):
    a = N['AUFNR']()
    wc_ops = ROUT[m]
    rsnum = N['RSNUM']()
    resb = []
    for i, (c, cq) in enumerate(BOM[m]):
        rq = cq * q
        resb.append(dict(rspos=f'{i + 1:04d}', matnr=c, werks=w, qty=rq, open=rq))
        T['RESB'].append(dict(RSNUM=rsnum, RSPOS=f'{i + 1:04d}', MATNR=c, WERKS=w, LGORT=SLOC(c, w), BDMNG=rq, ENMNG=0, MEINS='EA', AUFNR=a, BDTER=iso(start)))
    T['AUFK'].append(dict(AUFNR=a, AUART='PP01', AUTYP='10', WERKS=w, KTEXT=MATS[m][0], ERDAT=iso(d), KOKRS=C['kokrs'], PRCTR=PRCTR(m, w)))
    T['AFKO'].append(dict(AUFNR=a, PLNBEZ=m, GAMNG=q, GMEIN='EA', GSTRP=iso(start), GLTRP=iso(fin), FEVOR='P01' if w == '1110' else 'P02', RSNUM=rsnum, PLNUM=plnum))
    T['AFPO'].append(dict(AUFNR=a, POSNR='0001', MATNR=m, PSMNG=q, WEMNG=0, AMEIN='EA', LGORT=SLOC(m, w), PWERK=w))
    PROD[a] = dict(aufnr=a, matnr=m, werks=w, qty=q, start=start, fin=fin, gr=0, resb=resb, rsnum=rsnum, stat='CRTD', cost=0, credit=0, gi_done=False, conf_done=False, settled=False, created=d)
    ev('pro', d)
    return a

def convert_prs(d):
    rest = []
    by_sup = defaultdict(list)
    for pr in PRS_TO_CONVERT:
        if pr['d'] < d: by_sup[SUP_OF[pr['matnr']][0]].append(pr)
        else: rest.append(pr)
    for lifnr, prs in by_sup.items():
        s = SUPP[lifnr]; eb = N['EBELN'](); items = []; tot = 0
        for i, pr in enumerate(prs):
            ebelp = f'{(i + 1) * 10:05d}'
            price = INFO_PRICE[pr['matnr']]
            eindt = max(pr['need'], addb(d, MATS[pr['matnr']][9]))
            items.append(dict(ebelp=ebelp, matnr=pr['matnr'], werks=pr['werks'], qty=pr['qty'], price=price, eindt=eindt, gr=0, ir=0, banfn=pr['banfn']))
            tot += pr['qty'] * price
            T['EKPO'].append(dict(EBELN=eb, EBELP=ebelp, MATNR=pr['matnr'], TXZ01=MATS[pr['matnr']][0], MENGE=pr['qty'], MEINS='EA', NETPR=price, PEINH=1,
                                  NETWR=pr['qty'] * price, WERKS=pr['werks'], LGORT=SLOC(pr['matnr'], pr['werks']), KNTTP='', BANFN=pr['banfn'], BNFPO='00010', ELIKZ='', EREKZ='', INSMK='X' if MATS[pr['matnr']][10] else ''))
            T['EKET'].append(dict(EBELN=eb, EBELP=ebelp, ETENR='0001', EINDT=iso(eindt), MENGE=pr['qty'], WEMNG=0))
            for r in T['EBAN']:
                if r['BANFN'] == pr['banfn']: r['EBELN'] = eb; r['EBELP'] = ebelp
            FLOW.append(('EBAN', pr['banfn'], 'EKKO', eb))
            late = R.choices([-1, 0, 0, 0, 1, 2, 4], [1, 5, 5, 5, 3, 2, 1])[0]
            PEND_GR.append((addb(eindt, late) if late >= 0 else eindt - dt.timedelta(1), eb, ebelp))
        grp = 'P03' if MATS[prs[0]['matnr']][1] == 'HAWA' else ('P01' if MATS[prs[0]['matnr']][2].startswith('EL') else 'P02')
        T['EKKO'].append(dict(EBELN=eb, BSART='NB', LIFNR=lifnr, EKORG='1100', EKGRP=grp, BUKRS=C['bukrs'], BEDAT=iso(d), WAERS='KRW', ZTERM=s[3], NETWR=tot))
        PO[eb] = dict(ebeln=eb, lifnr=lifnr, items=items, d=d)
        ev('po', d)
    PRS_TO_CONVERT[:] = rest

def goods_receipts(d):
    global PEND_GR
    keep = []
    due_now = defaultdict(list)
    for gd, eb, ep in PEND_GR:
        if next_bday(gd) <= d: due_now[eb].append(ep)
        else: keep.append((gd, eb, ep))
    for eb, eps in due_now.items():
        po = PO[eb]; mitems = []; lines = []
        xb = f'DN-{R.randint(10000, 99999)}'
        for ep in eps:
            it = next(i for i in po['items'] if i['ebelp'] == ep)
            m, w, q = it['matnr'], it['werks'], it['qty'] - it['gr']
            qm = MATS[m][10]
            mitems.append(dict(matnr=m, werks=w, menge=q, dmbtr=q * STD[m], ebeln=eb, ebelp=ep, lifnr=po['lifnr'], insmk='Q' if qm else 'U'))
            it['gr'] += q
            val_std = q * STD[m]; val_po = q * it['price']; pc = PRCTR(m, w)
            lines.append(dict(racct=INV_ACCT[MATS[m][1]], hsl=val_std, ktosl='BSX', matnr=m, werks=w, prctr=pc, msl=q, runit='EA'))
            if val_po != val_std: lines.append(dict(racct='532000', hsl=val_po - val_std, ktosl='PRD', matnr=m, werks=w, prctr=pc, sgtxt='구매 가격차이'))
            lines.append(dict(racct='211900', hsl=-val_po, ktosl='WRX', matnr=m, werks=w, lifnr=po['lifnr'], prctr=pc, msl=-q, runit='EA'))
            for r in T['EKET']:
                if r['EBELN'] == eb and r['EBELP'] == ep: r['WEMNG'] = it['gr']
            for r in T['EKPO']:
                if r['EBELN'] == eb and r['EBELP'] == ep: r['ELIKZ'] = 'X'
        mb = matdoc(d, '101', mitems, xb)
        FLOW.append(('EKKO', eb, 'MATDOC', mb))
        fi = post('WE', d, lines, 'MKPF', mb + str(d.year), '입고 ' + eb, xb)
        FLOW.append(('MATDOC', mb, 'BKPF', fi))
        for mi in mitems:
            if mi['insmk'] == 'Q':
                pl = N['QALS']()
                T['QALS'].append(dict(PRUEFLOS=pl, HERKUNFT='01', ART='01', WERK=mi['werks'], MATNR=mi['matnr'], LOSMENGE=mi['menge'], MENGENEINH='EA', EBELN=eb, EBELP=mi['ebelp'], MBLNR=mb, MJAHR=d.year, ENSTEHDAT=iso(d), LIFNR=po['lifnr']))
                QI_LOTS.append((addb(d, R.choice([1, 1, 2])), pl, mi['matnr'], mi['werks'], mi['menge'], mb))
                FLOW.append(('MATDOC', mb, 'QALS', pl))
        PEND_IV.append((addb(d, R.randint(2, 6)), eb, eps, mb))
        ev('gr', d)
    PEND_GR = keep
PEND_IV = []

def usage_decisions(d):
    rest = []
    for ud, pl, m, w, q, mb in QI_LOTS:
        if ud <= d:
            T['QAVE'].append(dict(PRUEFLOS=pl, VCODE='A', VDATUM=iso(d), VNAME='QM01', KZART='L'))
            mb2 = matdoc(d, '321', [dict(matnr=m, werks=w, menge=q, insmk='U')], '', '사용결정')
            FLOW.append(('QALS', pl, 'MATDOC', mb2))
            ev('qm', d)
        else: rest.append((ud, pl, m, w, q, mb))
    QI_LOTS[:] = rest

def invoices(d):
    global PEND_IV
    keep = []
    for idt, eb, eps, mb in PEND_IV:
        if idt > d: keep.append((idt, eb, eps, mb)); continue
        po = PO[eb]; s = SUPP[po['lifnr']]
        belnr = N['RBKP'](); net = 0; rows = []; lines = []
        for k, ep in enumerate(eps):
            it = next(i for i in po['items'] if i['ebelp'] == ep)
            q = it['gr'] - it['ir']; amt = q * it['price']; net += amt; it['ir'] += q
            rows.append(dict(BELNR=belnr, GJAHR=d.year, BUZEI=f'{k + 1:06d}', EBELN=eb, EBELP=ep, MATNR=it['matnr'], MENGE=q, BSTME='EA', WRBTR=amt, WERKS=it['werks']))
            lines.append(dict(racct='211900', hsl=amt, ktosl='WRX', matnr=it['matnr'], werks=it['werks'], lifnr=po['lifnr'], prctr=PRCTR(it['matnr'], it['werks']), msl=q, runit='EA'))
            for r in T['EKPO']:
                if r['EBELN'] == eb and r['EBELP'] == ep: r['EREKZ'] = 'X'
        tax = int(round(net * VAT)); gross = net + tax
        lines.append(dict(racct='114100', hsl=tax, ktosl='VST', sgtxt='매입 부가세'))
        lines.insert(0, dict(racct='211100', hsl=-gross, lifnr=po['lifnr'], sgtxt='공급업체 채무'))
        fi = post('RE', d, lines, 'RMRP', belnr + str(d.year), '송장 ' + eb, f'INV-{R.randint(100000, 999999)}')
        T['RBKP'].append(dict(BELNR=belnr, GJAHR=d.year, BLART='RE', BLDAT=iso(d - dt.timedelta(1)), BUDAT=iso(d), LIFNR=po['lifnr'], RMWWR=gross, WMWST1=tax, WAERS='KRW', ZTERM=s[3], XBLNR=lines and ''))
        T['RSEG'].extend(rows)
        FLOW.append(('EKKO', eb, 'RBKP', belnr)); FLOW.append(('RBKP', belnr, 'BKPF', fi))
        OPEN_AP.append(dict(rbkp=belnr, fi=fi, lifnr=po['lifnr'], due=DUE(d, s[3]), gross=gross))
        ev('iv', d)
    PEND_IV = keep

def payment_run(d):
    if d.weekday() != 3: return
    horizon = d + dt.timedelta(7)
    pay = [ap for ap in OPEN_AP if ap['due'] <= horizon]
    if not pay: return
    by = defaultdict(list)
    for ap in pay: by[ap['lifnr']].append(ap)
    for lifnr, aps in by.items():
        tot = sum(a['gross'] for a in aps)
        fi = post('KZ', d, [dict(racct='211100', hsl=tot, lifnr=lifnr, sgtxt='채무 반제'), dict(racct='110100', hsl=-tot, sgtxt='자동 지급 F110')], 'BKPF', 'KZ', f'F110 {iso(d)}', '', 'KRW')
        T['REGUH'].append(dict(LAUFD=iso(d), LAUFI='GA' + d.strftime('%m%d'), LIFNR=lifnr, VBLNR=fi, RBETR=tot, WAERS='KRW', ZLSCH='T'))
        for a in aps:
            T['BSE_CLR'].append(dict(BUKRS=C['bukrs'], BELNR=a['fi'], AUGBL=fi, AUGDT=iso(d), KUNNR='', LIFNR=lifnr))
            FLOW.append(('BKPF', a['fi'], 'BKPF', fi))
            OPEN_AP.remove(a)
        ev('payout', d)

def production(d):
    committed = defaultdict(float)
    for a, p in sorted(PROD.items(), key=lambda kv: kv[1]['start']):
        if p['stat'] == 'CRTD' and p['start'] <= d:
            p['stat'] = 'REL'
        if p['stat'] == 'REL' and not p['gi_done']:
            if not all(stock(r['matnr'], r['werks']) - committed[(r['matnr'], r['werks'])] >= r['open'] for r in p['resb']):
                for r in p['resb']: committed[(r['matnr'], r['werks'])] += r['open']
            if all(stock(r['matnr'], r['werks']) - committed[(r['matnr'], r['werks'])] >= r['open'] for r in p['resb']):
                mitems = []; lines = []; tot = 0
                for r in p['resb']:
                    m = r['matnr']; q = r['open']; val = q * STD[m]; tot += val
                    mitems.append(dict(matnr=m, werks=r['werks'], menge=q, dmbtr=val, aufnr=a, rsnum=p['rsnum'], rspos=r['rspos']))
                    lines += [dict(racct='520100', hsl=val, ktosl='GBB', aufnr=a, matnr=m, werks=r['werks'], prctr=PRCTR(p['matnr'], p['werks']), msl=q, runit='EA', sgtxt='부품 투입'),
                              dict(racct=INV_ACCT[MATS[m][1]], hsl=-val, ktosl='BSX', matnr=m, werks=r['werks'], prctr=PRCTR(m, r['werks']), msl=-q, runit='EA')]
                    r['open'] = 0
                    for x in T['RESB']:
                        if x['RSNUM'] == p['rsnum'] and x['RSPOS'] == r['rspos']: x['ENMNG'] = q
                mb = matdoc(d, '261', mitems)
                fi = post('WA', d, lines, 'MKPF', mb + str(d.year), '부품 출고 ' + a)
                FLOW.append(('AUFK', a, 'MATDOC', mb)); FLOW.append(('MATDOC', mb, 'BKPF', fi))
                p['cost'] += tot; p['gi_done'] = True; p['gi_day'] = d
                dur = max(1, math.ceil(p['qty'] * sum(h for _, _, h in ROUT[p['matnr']]) / 24))
                p['fin_act'] = addb(d, dur)
                ev('gi', d)
            elif d > addb(p['start'], 1):
                p['delayed'] = True
        if p['gi_done'] and not p['conf_done'] and p.get('fin_act') and p['fin_act'] <= d:
            m, w = p['matnr'], p['werks']
            eff = R.uniform(0.92, 1.18)
            for vornr, wcn, h in ROUT[m]:
                hrs = round(p['qty'] * h * eff, 1)
                wcd = WC[wcn]; val = int(round(hrs * wcd[3]))
                rueck = N['RUECK']()
                T['AFRU'].append(dict(RUECK=rueck, RMZHL='00000001', AUFNR=a, VORNR=vornr, ARBID=WC_OBJ[wcn], LMNGA=p['qty'], MEINH='EA', ISM01=hrs, ILE01='H', BUDAT=iso(d), LTXA1='완료 확인'))
                acct = '943100' if wcd[2] == 'ASM' else '943200'
                co = N['COBK']()
                post('CO', d, [dict(racct=acct, hsl=val, aufnr=a, prctr=PRCTR(m, w), msl=hrs, runit='H', sgtxt=f'{wcd[2]} {hrs}H'),
                               dict(racct=acct, hsl=-val, rcntr=wcd[1], prctr=CC_PC[wcd[1]], msl=-hrs, runit='H', sgtxt=f'{wcd[2]} 활동 배분')], 'COBK', co, '실적 확인 ' + a)
                p['cost'] += val
                FLOW.append(('AUFK', a, 'AFRU', rueck))
                ev('conf', d)
            p['conf_done'] = True
            q = p['qty']; val = q * STD[m]
            mb = matdoc(d, '101', [dict(matnr=m, werks=w, menge=q, dmbtr=val, aufnr=a)])
            fi = post('WE', d, [dict(racct=INV_ACCT[MATS[m][1]], hsl=val, ktosl='BSX', matnr=m, werks=w, prctr=PRCTR(m, w), msl=q, runit='EA'),
                                dict(racct='520900', hsl=-val, ktosl='GBB', aufnr=a, matnr=m, werks=w, prctr=PRCTR(m, w), msl=-q, runit='EA', sgtxt='생산 입고')], 'MKPF', mb + str(d.year), '생산 입고 ' + a)
            FLOW.append(('AUFK', a, 'MATDOC', mb)); FLOW.append(('MATDOC', mb, 'BKPF', fi))
            p['gr'] = q; p['credit'] += val; p['stat'] = 'DLV'; p['gr_day'] = d
            for r in T['AFPO']:
                if r['AUFNR'] == a: r['WEMNG'] = q
            ev('grp', d)

def month_end(d):
    ym = (d.year, d.month)
    # 급여 (25일 전후 영업일)
    lines = []; tot = 0
    for k, v in C['kostl'].items():
        amt = int(round(v[3] * R.uniform(0.98, 1.03), -3)); tot += amt
        lines.append(dict(racct='610000', hsl=amt, rcntr=k, prctr=CC_PC[k], sgtxt='급여'))
    lines.append(dict(racct='253000', hsl=-tot, sgtxt='미지급 급여'))
    pd_ = next_bday(dt.date(d.year, d.month, 25))
    post('SA', pd_, lines, 'BKPF', 'HR', f'{d.month}월 급여 (인사 급여 전표)')
    post('SA', pd_, [dict(racct='253000', hsl=tot), dict(racct='110100', hsl=-tot)], 'BKPF', 'HR', f'{d.month}월 급여 지급')
    ev('je', pd_, 2)
    # 전력·임차료
    lines = []; tot = 0
    for k, v in C['kostl'].items():
        if v[4]:
            amt = int(round(v[4] * R.uniform(0.9, 1.12), -3)); tot += amt
            lines.append(dict(racct='630000', hsl=amt, rcntr=k, prctr=CC_PC[k], sgtxt='전력비'))
    lines.append(dict(racct='110100', hsl=-tot)); post('SA', d, lines, 'BKPF', 'UTIL', f'{d.month}월 전력·수도비'); ev('je', d)
    rk, ra = C['rent']
    post('SA', d, [dict(racct='640000', hsl=ra, rcntr=rk, prctr=CC_PC[rk], sgtxt='본사 임차료'), dict(racct='110100', hsl=-ra)], 'BKPF', 'RENT', f'{d.month}월 임차료'); ev('je', d)
    # 감가상각
    lines = []
    for a in C['assets']:
        acc = '151900' if a[1] == '3000' else '152900'
        lines += [dict(racct='620000', hsl=a[5], rcntr=a[3], prctr=CC_PC[a[3]], anln1=a[0], sgtxt=a[2]), dict(racct=acc, hsl=-a[5], anln1=a[0])]
    post('AF', d, lines, 'AMDP', f'{d.year}{d.month:02d}', f'{d.month}월 감가상각 (AFAB)'); ev('dep', d)
    # 배부 (보조 원가센터 → 수혜 원가센터)
    bal = defaultdict(int)
    for r in T['ACDOCA']:
        if r['RCNTR'] and r['BUDAT'][:7] == f'{d.year}-{d.month:02d}': bal[r['RCNTR']] += r['HSL']
    for sender in ['4300', '7200', '7100']:
        amt = bal[sender]
        if amt <= 0: continue
        rec = C['assess'][sender]; lines = []; done = 0; keys = list(rec)
        for i, k in enumerate(keys):
            part = amt - done if i == len(keys) - 1 else int(round(amt * rec[k] / 100))
            done += part; bal[k] += part
            lines.append(dict(racct='942000', hsl=part, rcntr=k, prctr=CC_PC[k], sgtxt=f'{sender} 배부'))
        lines.append(dict(racct='942000', hsl=-amt, rcntr=sender, prctr=CC_PC[sender], sgtxt='배부 송신'))
        bal[sender] = 0
        post('CO', d, lines, 'COBK', N['COBK'](), f'{d.month}월 배부 {sender}'); ev('alloc', d)
    # 생산오더 정산: 이번 달 입고 완료된 오더
    for a, p in PROD.items():
        if p['stat'] == 'DLV' and not p['settled'] and p['gr_day'] <= d:
            var = p['cost'] - p['credit']
            m, w = p['matnr'], p['werks']
            if var != 0:
                fi = post('CO', d, [dict(racct='531000', hsl=var, ktosl='PRD', matnr=m, werks=w, prctr=PRCTR(m, w), sgtxt='생산 차이'),
                                    dict(racct='520950', hsl=-var, aufnr=a, matnr=m, werks=w, prctr=PRCTR(m, w), sgtxt='오더 정산')], 'AUFK', a, f'정산 {a}')
                FLOW.append(('AUFK', a, 'BKPF', fi))
            p['settled'] = True; p['var'] = var; p['stat'] = 'DLV TECO' if False else 'DLV'
            T['SETTLE'].append(dict(AUFNR=a, PERIO=f'{d.month:03d}', GJAHR=d.year, MATNR=m, ISTKOSTEN=p['cost'], ENTLASTUNG=p['credit'], ABWEICHUNG=var))
            ev('stl', d)

# ════════════════════════════════ 시뮬레이션 ════════════════════════════════
month_last = {}
for d in BDAYS: month_last[(d.year, d.month)] = d
# 7월 이월 수주 (기간 시작 전 받은 주문)
for i in range(10):
    bd = OPEN - dt.timedelta(13 - i)
    if bd.weekday() < 5:
        for _ in range(R.choices([2, 3, 4], [3, 4, 2])[0]): create_so(bd)
for d in BDAYS:
    if d.weekday() in (0, 2, 4) or d == BDAYS[0]: run_mrp(d)
    convert_prs(d)
    goods_receipts(d)
    usage_decisions(d)
    invoices(d)
    production(d)
    for _ in range(R.choices([2, 3, 4, 5], [2, 4, 3, 2])[0]): create_so(d)
    deliver(d)
    bill(d)
    receive_payments(d)
    payment_run(d)
    if d == month_last[(d.year, d.month)]: month_end(d)

# 상태 정리
for vb, so in SO.items():
    for r in T['VBAP']:
        if r['VBELN'] == vb:
            it = next(i for i in so['items'] if i['posnr'] == r['POSNR'])
            r['GBSTA'] = 'C' if it.get('billed', 0) >= it['qty'] else ('B' if it['open'] == 0 else 'A')
for a, p in PROD.items():
    T['JEST_TXT'].append(dict(AUFNR=a, STTXT={'CRTD': 'CRTD', 'REL': 'REL' + (' MSPT' if p.get('delayed') else ''), 'DLV': 'REL CNF DLV'}[p['stat']] + (' SETC' if p['settled'] else '')))
OPEN_ITEMS = dict(ar=[dict(VBELN=a['vbrk'], BELNR=a['fi'], KUNNR=a['kunnr'], DUE=iso(a['duec']), HSL=a['hsl'], WSL=a['wsl'], CUR=a['cur']) for a in OPEN_AR],
                  ap=[dict(RBKP=a['rbkp'], BELNR=a['fi'], LIFNR=a['lifnr'], DUE=iso(a['due']), HSL=a['gross']) for a in OPEN_AP])

# ════════════════════════════════ 검증 ════════════════════════════════
by_doc = defaultdict(int)
for r in T['ACDOCA']: by_doc[r['BELNR']] += r['HSL']
assert all(abs(v) < 1e-6 for v in by_doc.values()), 'unbalanced'
assert abs(sum(r['HSL'] for r in T['ACDOCA'])) < 1e-6
# 재고 금액 = 재고 계정 잔액
inv_val = sum(q * STD[m] for (m, w, t), q in STOCK.items())
inv_gl = sum(r['HSL'] for r in T['ACDOCA'] if r['RACCT'] in INV_ACCT.values())
assert abs(inv_val - inv_gl) < 1, (inv_val, inv_gl)
# AR 잔액 = 미결
ar_gl = sum(r['HSL'] for r in T['ACDOCA'] if r['RACCT'] == '113100')
assert abs(ar_gl - sum(a['hsl'] for a in OPEN_AR)) < 1
ap_gl = sum(r['HSL'] for r in T['ACDOCA'] if r['RACCT'] == '211100')
assert abs(ap_gl + sum(a['gross'] for a in OPEN_AP)) < 1
grir = sum(r['HSL'] for r in T['ACDOCA'] if r['RACCT'] == '211900')

# ════════════════════════════════ 대표 문서 (설명 템플릿용) ════════════════════════════════
def first(rows, **kw): return next(r for r in rows if all(r.get(k) == v for k, v in kw.items()))
def lines_of(belnr): return [dict(a=r['RACCT'], n=GLN[r['RACCT']], h=r['HSL'], k=r['KTOSL'], cc=r['RCNTR'], o=r['AUFNR']) for r in T['ACDOCA'] if r['BELNR'] == belnr]
GLN = {g[0]: g[1] for g in GL}
paid_so = None
for vb in SO:
    so = SO[vb]
    if so['head']['WAERK'] != 'KRW' or so['head']['GBSTK'] != 'C' or len(so['items']) < 2: continue
    if dt.date.fromisoformat(so['head']['ERDAT']) < addb(START, 5): continue
    lks = [x[3] for x in FLOW if x[0] == 'VBAK' and x[1] == vb]
    if len(set(lks)) != 1 or any(r['WADAT_IST'] > so['head']['VDATU'] for r in T['LIKP'] if r['VBELN'] in lks): continue
    vbrks = [f[3] for f in FLOW if f[0] == 'LIKP' and f[1] in [x[3] for x in FLOW if x[0] == 'VBAK' and x[1] == vb]]
    if not vbrks: continue
    fis = [f[3] for f in FLOW if f[0] == 'VBRK' and f[1] in vbrks]
    if any(any(c['BELNR'] == fi for c in T['BSE_CLR']) for fi in fis) and so['cust'][5] == '10':
        paid_so = vb; break
so = SO[paid_so]; hd = so['head']
lk = next(f[3] for f in FLOW if f[0] == 'VBAK' and f[1] == paid_so and f[2] == 'LIKP')
pgi_mb = next(f[3] for f in FLOW if f[0] == 'LIKP' and f[1] == lk and f[2] == 'MATDOC')
pgi_fi = next(f[3] for f in FLOW if f[0] == 'MATDOC' and f[1] == pgi_mb and f[2] == 'BKPF')
vb = next(f[3] for f in FLOW if f[0] == 'LIKP' and f[1] == lk and f[2] == 'VBRK')
rv = next(f[3] for f in FLOW if f[0] == 'VBRK' and f[1] == vb and f[2] == 'BKPF')
dz = next(c['AUGBL'] for c in T['BSE_CLR'] if c['BELNR'] == rv)
vbrk = first(T['VBRK'], VBELN=vb)
it0 = so['items'][0]
FEAT = {}
FEAT['so'] = dict(no=paid_so, auart=hd['AUART'], vkorg=hd['VKORG'], vkorgName=C['vkorgs'][hd['VKORG']], vtweg=hd['VTWEG'], vtwegName=C['vtwegs'][hd['VTWEG']], spart=hd['SPART'], spartName=C['spart'][hd['SPART']],
                  kunnr=hd['KUNNR'], kname=so['cust'][1], bstnk=hd['BSTNK'], erdat=hd['ERDAT'], vdatu=hd['VDATU'], netwr=hd['NETWR'], waerk=hd['WAERK'], zterm=hd['ZTERM'], inco=hd['INCO1'],
                  mat=it0['matnr'], matName=MATS[it0['matnr']][0], qty=it0['qty'], price=it0['price'], itemNet=it0['net'], werks=it0['werks'], plantName=C['plants'][it0['werks']]['name'], nItems=len(so['items']),
                  items=[dict(posnr=i['posnr'], mat=i['matnr'], name=MATS[i['matnr']][0], qty=i['qty'], price=i['price'], net=i['net'], werks=i['werks']) for i in so['items']])
FEAT['dlv'] = dict(no=lk, date=first(T['LIKP'], VBELN=lk)['WADAT_IST'], vstel=first(T['LIKP'], VBELN=lk)['VSTEL'])
FEAT['pgi'] = dict(mblnr=pgi_mb, fi=pgi_fi, lines=lines_of(pgi_fi), date=FEAT['dlv']['date'])
FEAT['bil'] = dict(no=vb, fi=rv, date=vbrk['FKDAT'], net=vbrk['NETWR'], tax=vbrk['MWSBK'], gross=vbrk['NETWR'] + vbrk['MWSBK'], lines=lines_of(rv))
FEAT['pay'] = dict(fi=dz, date=first(T['BKPF'], BELNR=dz)['BUDAT'], lines=lines_of(dz))
# 대표 생산오더: 대표 판매오더 자재, 입고·정산 완료, 차이 있음
cands = [p for p in PROD.values() if p['matnr'] == it0['matnr'] and p['settled'] and p['var'] and p['created'] >= addb(START, 10)] or [p for p in PROD.values() if MATS[p['matnr']][1] == 'FERT' and p['settled']]
pp_ = cands[0]; a = pp_['aufnr']
afko = first(T['AFKO'], AUFNR=a)
gi_mb = next(f[3] for f in FLOW if f[0] == 'AUFK' and f[1] == a and f[2] == 'MATDOC' and any(r['MBLNR'] == f[3] and r['BWART'] == '261' for r in T['MATDOC']))
gr_mb = next(f[3] for f in FLOW if f[0] == 'AUFK' and f[1] == a and f[2] == 'MATDOC' and any(r['MBLNR'] == f[3] and r['BWART'] == '101' for r in T['MATDOC']))
gi_fi = next(f[3] for f in FLOW if f[0] == 'MATDOC' and f[1] == gi_mb and f[2] == 'BKPF')
grp_fi = next(f[3] for f in FLOW if f[0] == 'MATDOC' and f[1] == gr_mb and f[2] == 'BKPF')
conf_rows = [r for r in T['AFRU'] if r['AUFNR'] == a]
conf_lines = [l for r in T['ACDOCA'] if r['AUFNR'] == a and r['RACCT'] in ('943100', '943200') for l in [r]]
co_docs = sorted({r['BELNR'] for r in T['ACDOCA'] if r['AUFNR'] == a and r['RACCT'] in ('943100', '943200')})
stl_doc = next((r['BELNR'] for r in T['ACDOCA'] if r['AUFNR'] == a and r['RACCT'] == '520950'), '')
plnum = afko['PLNUM']
FEAT['pro'] = dict(no=a, mat=pp_['matnr'], matName=MATS[pp_['matnr']][0], qty=pp_['qty'], werks=pp_['werks'], plantName=C['plants'][pp_['werks']]['name'], start=afko['GSTRP'], fin=afko['GLTRP'], plnum=plnum,
                   std=STD[pp_['matnr']], comps=[dict(mat=r['MATNR'], name=MATS[r['MATNR']][0], qty=r['BDMNG']) for r in T['RESB'] if r['AUFNR'] == a],
                   ops=[dict(vornr=v, wc=w, h=h, plan=round(h * pp_['qty'], 1), act=next(r['ISM01'] for r in conf_rows if r['VORNR'] == v), rate=WC[w][3], act_type=WC[w][2], kostl=WC[w][1]) for v, w, h in ROUT[pp_['matnr']]],
                   gi=dict(mblnr=gi_mb, fi=gi_fi, lines=lines_of(gi_fi), date=pp_['gi_day'].isoformat()), gr=dict(mblnr=gr_mb, fi=grp_fi, lines=lines_of(grp_fi), date=pp_['gr_day'].isoformat()),
                   conf=[dict(doc=c, lines=lines_of(c)) for c in co_docs], cost=pp_['cost'], credit=pp_['credit'], var=pp_['var'], stl=dict(doc=stl_doc, lines=lines_of(stl_doc) if stl_doc else []))
# MRP 실행 (대표 생산오더가 만들어진 날)
FEAT['mrp'] = dict(date=pp_['created'].isoformat(), planned=sum(1 for r in T['PLAF'] if r['PSTTR'] and PROD[next(f[3] for f in FLOW if f[0] == 'PLAF' and f[1] == r['PLNUM'])]['created'] == pp_['created']),
                   prs=sum(1 for r in T['EBAN'] if r['BADAT'] == pp_['created'].isoformat()))
# 대표 구매: 대표 생산오더 구성품을 산 구매오더 (QM 자재 우선), 입고·송장·지급 완료
po_pick = None
for eb, po in sorted(PO.items(), key=lambda kv: (len(kv[1]['items']) != 1, not MATS[kv[1]['items'][0]['matnr']][10], kv[0])):
    if all(i['ir'] >= i['qty'] for i in po['items']) and po['d'] >= addb(START, 10):
        rb = next((f[3] for f in FLOW if f[0] == 'EKKO' and f[1] == eb and f[2] == 'RBKP'), None)
        if not rb: continue
        refi = next(f[3] for f in FLOW if f[0] == 'RBKP' and f[1] == rb and f[2] == 'BKPF')
        if any(c['BELNR'] == refi for c in T['BSE_CLR']):
            po_pick = eb
            break
eb = po_pick; po = PO[eb]; ekko = first(T['EKKO'], EBELN=eb); pi0 = po['items'][0]
gr_mb2 = next(f[3] for f in FLOW if f[0] == 'EKKO' and f[1] == eb and f[2] == 'MATDOC')
we_fi = next(f[3] for f in FLOW if f[0] == 'MATDOC' and f[1] == gr_mb2 and f[2] == 'BKPF')
rb = next(f[3] for f in FLOW if f[0] == 'EKKO' and f[1] == eb and f[2] == 'RBKP')
re_fi = next(f[3] for f in FLOW if f[0] == 'RBKP' and f[1] == rb and f[2] == 'BKPF')
kz = next(c['AUGBL'] for c in T['BSE_CLR'] if c['BELNR'] == re_fi)
rbkp = first(T['RBKP'], BELNR=rb)
qals = [r for r in T['QALS'] if r['MBLNR'] == gr_mb2]
md = first(T['MATDOC'], MBLNR=gr_mb2)
FEAT['po'] = dict(no=eb, bsart='NB', lifnr=po['lifnr'], lname=SUPP[po['lifnr']][1], ekorg='1100', ekgrp=ekko['EKGRP'], ekgrpName=C['ekgrp'][ekko['EKGRP']], bedat=ekko['BEDAT'], netwr=ekko['NETWR'], zterm=ekko['ZTERM'],
                  mat=pi0['matnr'], matName=MATS[pi0['matnr']][0], qty=pi0['qty'], price=pi0['price'], std=STD[pi0['matnr']], werks=pi0['werks'], lgort=SLOC(pi0['matnr'], pi0['werks']), eindt=iso(pi0['eindt']), banfn=pi0['banfn'],
                  nItems=len(po['items']), items=[dict(ebelp=i['ebelp'], mat=i['matnr'], name=MATS[i['matnr']][0], qty=i['qty'], price=i['price'], werks=i['werks'], eindt=iso(i['eindt'])) for i in po['items']])
FEAT['gr'] = dict(mblnr=gr_mb2, fi=we_fi, date=md['BUDAT'], xblnr=md['XBLNR'], lines=lines_of(we_fi), insmk=md['INSMK'], qals=qals[0]['PRUEFLOS'] if qals else '', ud=next((r['VDATUM'] for r in T['QAVE'] if qals and r['PRUEFLOS'] == qals[0]['PRUEFLOS']), ''))
FEAT['iv'] = dict(no=rb, fi=re_fi, date=rbkp['BUDAT'], gross=rbkp['RMWWR'], tax=rbkp['WMWST1'], lines=lines_of(re_fi))
FEAT['payout'] = dict(fi=kz, date=first(T['BKPF'], BELNR=kz)['BUDAT'], lines=lines_of(kz))
# 대표 결산 문서 (마지막 달)
last_m = f'{END.year}-{END.month:02d}'
sa_docs = [r for r in T['BKPF'] if r['BLART'] == 'SA' and r['BUDAT'][:7] == last_m and r['AWKEY'] == 'RENT']
af_docs = [r for r in T['BKPF'] if r['BLART'] == 'AF' and r['BUDAT'][:7] == last_m]
al_docs = sorted({r['BELNR'] for r in T['ACDOCA'] if r['BLART'] == 'CO' and r['RACCT'] == '942000' and r['BUDAT'][:7] == last_m})
FEAT['je'] = dict(fi=sa_docs[0]['BELNR'], date=sa_docs[0]['BUDAT'], lines=lines_of(sa_docs[0]['BELNR']), text=sa_docs[0]['BKTXT'])
FEAT['dep'] = dict(fi=af_docs[0]['BELNR'], date=af_docs[0]['BUDAT'], lines=lines_of(af_docs[0]['BELNR']))
FEAT['alloc'] = dict(fi=al_docs[-1], date=next(r['BUDAT'] for r in T['ACDOCA'] if r['BELNR'] == al_docs[-1]), lines=lines_of(al_docs[-1]))
FEAT['kostl'] = dict(id='4110', name=C['kostl']['4110'][0], month=last_m)
FEAT['company'] = dict(name=C['name'], bukrs=C['bukrs'], kokrs=C['kokrs'], ktopl=C['ktopl'])

# ════════════════════════════════ 내보내기 ════════════════════════════════
META = {  # 테이블 설명: 모듈, 이름, 종류(org/master/trans/ctrl/cfg), 후속 CDS (S/4 공개 목록 기준, 없으면 '')
    'T001': ('FI', '회사코드', 'org', 'I_CompanyCode'), 'TKA01': ('CO', '관리회계 영역', 'org', 'I_ControllingArea'), 'T001W': ('MM', '플랜트', 'org', 'I_Plant'),
    'T001L': ('MM', '저장위치', 'org', 'I_StorageLocation'), 'TVST': ('SD', '출하지점', 'org', 'I_ShippingPoint'), 'TVKO': ('SD', '판매조직', 'org', 'I_SalesOrganization'),
    'TVTW': ('SD', '유통경로', 'org', 'I_DistributionChannel'), 'TSPA': ('SD', '제품군', 'org', 'I_Division'), 'T024E': ('MM', '구매조직', 'org', 'I_PurchasingOrganization'),
    'T024': ('MM', '구매그룹', 'org', 'I_PurchasingGroup'), 'CEPC': ('CO', '손익센터', 'org', 'I_ProfitCenter'), 'CSKS': ('CO', '원가센터', 'org', 'I_CostCenter'),
    'SKA1': ('FI', 'G/L 계정 (계정표)', 'master', 'I_GLAccountInChartOfAccounts'), 'SKB1': ('FI', 'G/L 계정 (회사코드)', 'master', 'I_GLAccountInCompanyCode'), 'CSKB': ('CO', '원가요소 (범주)', 'master', ''),
    'CSLA': ('CO', '활동 유형', 'master', ''), 'CRHD': ('PP', '작업장', 'master', 'I_WorkCenter'), 'CRCO': ('PP', '작업장-원가센터 연결', 'master', ''),
    'MARA': ('MM', '자재 일반', 'master', 'I_Product'), 'MAKT': ('MM', '자재 내역', 'master', 'I_ProductDescription'), 'MARC': ('MM', '자재 플랜트 (MRP)', 'master', 'I_ProductPlantBasic'),
    'MBEW': ('MM', '자재 평가', 'master', ''), 'MVKE': ('SD', '자재 판매 데이터', 'master', 'I_ProductSalesDelivery'), 'KONP': ('SD', '가격 조건', 'master', ''),
    'MAST': ('PP', '자재-BOM 연결', 'master', ''), 'STPO': ('PP', 'BOM 구성품', 'master', ''), 'PLKO': ('PP', '라우팅 헤더', 'master', 'I_BillOfOperationsGroup'), 'PLPO': ('PP', '라우팅 공정', 'master', 'I_MfgBillOfOperationsOperation'),
    'BUT000': ('BP', '비즈니스 파트너', 'master', 'I_BusinessPartner'), 'BUT100': ('BP', 'BP 역할', 'master', ''), 'KNA1': ('SD', '고객 일반', 'master', 'I_Customer'),
    'KNB1': ('FI', '고객 회사코드', 'master', 'I_CustomerCompany'), 'KNVV': ('SD', '고객 판매 영역', 'master', 'I_CustomerSalesArea'), 'LFA1': ('MM', '공급업체 일반', 'master', 'I_Supplier'),
    'LFB1': ('FI', '공급업체 회사코드', 'master', 'I_SupplierCompany'), 'LFM1': ('MM', '공급업체 구매조직', 'master', 'I_SupplierPurchasingOrg'), 'EINA': ('MM', '구매 정보 레코드', 'master', ''), 'EINE': ('MM', '정보 레코드 조건', 'master', ''),
    'ANLA': ('FI-AA', '고정자산', 'master', ''), 'ANLZ': ('FI-AA', '자산 원가센터 배정', 'master', ''),
    'VBAK': ('SD', '판매오더 헤더', 'trans', 'I_SalesDocument'), 'VBAP': ('SD', '판매오더 아이템', 'trans', 'I_SalesDocumentItem'), 'LIKP': ('SD', '출하문서 헤더', 'trans', 'I_DeliveryDocument'),
    'LIPS': ('SD', '출하문서 아이템', 'trans', 'I_DeliveryDocumentItem'), 'VBRK': ('SD', '청구문서 헤더', 'trans', 'I_BillingDocumentBasic'), 'VBRP': ('SD', '청구문서 아이템', 'trans', 'I_BillingDocumentItemBasic'),
    'EBAN': ('MM', '구매요청', 'trans', 'I_PurchaseRequisitionItemAPI01'), 'EKKO': ('MM', '구매오더 헤더', 'trans', 'I_PurchaseOrderAPI01'), 'EKPO': ('MM', '구매오더 아이템', 'trans', 'I_PurchaseOrderItemAPI01'),
    'EKET': ('MM', '구매오더 일정 라인', 'trans', 'I_PurOrdScheduleLineAPI01'), 'MATDOC': ('MM', '자재문서 (S/4)', 'trans', 'I_MaterialDocumentItem_2'), 'RBKP': ('MM', '송장 헤더', 'trans', 'I_SupplierInvoiceAPI01'),
    'RSEG': ('MM', '송장 아이템', 'trans', 'I_SuplrInvcItemPurOrdRefAPI01'), 'QALS': ('QM', '검사로트', 'trans', 'I_InspectionLot'), 'QAVE': ('QM', '사용결정', 'trans', ''),
    'PLAF': ('PP', '계획오더', 'trans', 'I_PlannedOrder'), 'AUFK': ('PP', '오더 마스터', 'trans', 'I_Order'), 'AFKO': ('PP', '생산오더 헤더', 'trans', 'I_ManufacturingOrder'), 'AFPO': ('PP', '생산오더 아이템', 'trans', 'I_ManufacturingOrderItem'),
    'RESB': ('PP', '예약 (부품 소요)', 'trans', 'I_ReservationDocumentItem'), 'AFRU': ('PP', '실적 확인', 'trans', 'I_MfgOrderConfirmation'),
    'BKPF': ('FI', '회계 전표 헤더', 'trans', 'I_JournalEntry'), 'ACDOCA': ('FI', 'Universal Journal 라인', 'trans', 'I_JournalEntryItem'), 'REGUH': ('FI', '지급 실행 결과', 'trans', ''),
}
VIRT = {'BSE_CLR': ('FI', '반제 내역 (교육용 요약 뷰)', 'trans', ''), 'JEST_TXT': ('PP', '오더 상태 (교육용 요약 뷰)', 'trans', ''), 'SETTLE': ('CO', '오더 정산 결과 (교육용 요약 뷰)', 'trans', '')}
tables = {}
for name, rows in T.items():
    if not rows: continue
    fields = list(rows[0].keys())
    for r in rows:
        for k in r:
            if k not in fields: fields.append(k)
    meta = META.get(name) or VIRT.get(name)
    tables[name] = dict(module=meta[0], desc=meta[1], kind=meta[2], cds=meta[3], virtual=name in VIRT, fields=fields, rows=[[r.get(f, '') for f in fields] for r in rows])
flow = sorted(set(FLOW), key=FLOW.index)
out = dict(schema='sap-edu-company/1', company=dict(id=C['id'], name=C['name'], nameEn=C['nameEn'], industry=C['industry'], bukrs=C['bukrs'], kokrs=C['kokrs'], ktopl=C['ktopl'],
            waers='KRW', fx=C['fx'], period=[C['start'], C['end']], opening=C['opening'], vat=VAT, seed=C['seed'], plants={k: v['name'] for k, v in C['plants'].items()}),
           tables=tables, flow=[list(f) for f in flow], events={k: dict(v) for k, v in EV.items()}, featured=FEAT, openItems=OPEN_ITEMS,
           std={m: STD[m] for m in MATS}, stock=[[m, w, t, q] for (m, w, t), q in STOCK.items() if q], gl={g[0]: dict(n=g[1], t=g[2], cat=g[3]) for g in GL})
if __name__ == '__main__':
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else f"{C['id']}.json"
    s = json.dumps(out, ensure_ascii=False, separators=(',', ':'))
    open(path, 'w').write(s)
    print('written', path, len(s.encode()) // 1024, 'KB')
    for k in sorted(tables, key=lambda x: -len(tables[x]['rows']))[:20]: print(f'  {k:8s} {len(tables[k]["rows"]):5d}')
    print('SO', len(SO), 'PO', len(PO), 'PROD', len(PROD), 'ACDOCA', len(T['ACDOCA']), 'BKPF', len(T['BKPF']), 'open AR', len(OPEN_AR), 'open AP', len(OPEN_AP), 'GR/IR', grir)
    print('featured SO', paid_so, 'PO', eb, 'PROD', a)

def _diag():
    import collections
    short = collections.Counter()
    for a, p in PROD.items():
        if p['stat'] == 'REL' and not p['gi_done']:
            for r in p['resb']:
                if stock(r['matnr'], r['werks']) < r['open']: short[(r['matnr'], r['werks'])] += 1
    print('short comps', short.most_common(10))
    old = [(a, p['matnr'], p['qty'], p['start']) for a, p in PROD.items() if p['stat'] == 'REL' and not p['gi_done']]
    print('waiting orders', sorted(old, key=lambda x: x[3])[:10])
    for m in ['MOT-24', 'PCB-AIR', 'SEN-PM', 'ULT-01', 'FLT-H13', 'SA-FAN', 'SA-ACT', 'CRD-KR', 'BOX-M']:
        for w in MATS[m][3]:
            openpo = sum(it['qty'] - it['gr'] for po in PO.values() for it in po['items'] if it['matnr'] == m and it['werks'] == w)
            print(m, w, 'U', stock(m, w, 'U'), 'Q', stock(m, w, 'Q'), 'openPO', openpo, 'resb', sum(r['open'] for p in PROD.values() for r in p['resb'] if r['matnr'] == m and r['werks'] == w))
if __name__ == '__main__' and len(__import__('sys').argv) > 2: _diag()
